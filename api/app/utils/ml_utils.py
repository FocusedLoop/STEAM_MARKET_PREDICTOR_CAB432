import pandas as pd
import numpy as np
import hashlib
import io
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from .utils_redis import RedisJobQueue
from .utils_s3 import S3StorageManager
import os, json, threading, time, uuid, base64

# Global Redis job queue instance
redis_job_queue = RedisJobQueue()

# Global S3 storage manager instance
s3_storage_manager = S3StorageManager()

# Validate json price history structure
def validate_price_history(price_history: dict):
    if not isinstance(price_history, dict):
        return False, "Price history must be a dictionary"
    prices = price_history.get("prices")
    if not isinstance(prices, list) or not prices:
        return False, "Missing or invalid 'prices' list"
    for entry in prices:
        if not (isinstance(entry, list) and len(entry) == 3):
            return False, "Each price entry must be a list of [date, price, quantity]"
        date, price, quantity = entry
        if not isinstance(date, str):
            return False, "Date must be a string"
        try:
            float(price)
        except (ValueError, TypeError):
            return False, "Price must be a number"
        if not (isinstance(quantity, (str, int))):
            return False, "Quantity must be a string or integer"
    return True, ""

class PriceModel:
    """
    PriceModel provides methods to train, save, and use a machine learning model for predicting item prices over time.
    It handles data normalization, model training, evaluation, saving/loading model artifacts, and generating prediction graphs.
    Designed for use with time series price data, it generates future price predictions (utilizing random forests).
    """

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    QUEUE_STATUS_PATH = os.path.join(BASE_DIR, "tmp/queue_status.txt")
    MODEL_DIR = os.path.join(BASE_DIR, "tmp/models/")
    SCALER_DIR = os.path.join(BASE_DIR, "tmp/scalers/")
    FEATURES_DIR = os.path.join(BASE_DIR, "tmp/features/")

    # Shared Redis-based queue for all training instances
    _worker_started = False

    def __init__(self, user_id: int, username: str, item_id: int, item_name: str):
        self.user_id = user_id
        self.username = username
        self.item_id = item_id
        self.item_name = item_name

        self.feature_cols = [
            "time_numeric", "volume", "day_of_week", "month", "year", "day",
            "is_weekend", "price_rolling_mean_7", "price_diff", "volume_rolling_mean_7"
        ]
    
    # Update _start_worker to use RedisJobQueue method
    def _start_worker(self):
        if not PriceModel._worker_started:
            PriceModel._worker_started = True
            worker_thread = threading.Thread(target=redis_job_queue.redis_queue_worker, args=(PriceModel,), daemon=True)
            worker_thread.start()

    # Update _train_and_eval to use dynamic check
    def _train_and_eval_redis(self, raw_prices: str):
        job_id = str(uuid.uuid4())
        job_data = {
            "func": "_train_and_eval_actual",
            "args": [self.user_id, self.username, self.item_id, self.item_name, raw_prices],
            "kwargs": {},
            "timestamp": time.time(),
            "job_id": job_id
        }
        redis_job_queue.enqueue(job_data)
        self._start_worker()
        
        # Wait for result
        while True:
            result_str = redis_job_queue.redis_client.get(f"job_result:{job_id}")
            if result_str:
                result_dict = json.loads(result_str)
                if "error" in result_dict:
                    raise RuntimeError(result_dict["error"])
                # Deserialize
                pipe = joblib.load(io.BytesIO(base64.b64decode(result_dict["pipe"])))
                scaler = joblib.load(io.BytesIO(base64.b64decode(result_dict["scaler"])))
                df = pd.read_json(io.StringIO(result_dict["df"]))
                metrics = json.loads(result_dict["metrics"])
                # Clean up
                redis_job_queue.redis_client.delete(f"job_result:{job_id}")
                return pipe, scaler, df, metrics
            time.sleep(1)
    
    # Normalize price data
    @staticmethod
    def _normalize_prices(raw_prices: list):
        # Create dataframe for primary features
        df = pd.DataFrame(raw_prices)
        df[['time', 'price', 'volume']] = pd.DataFrame(df['prices'].tolist(), index=df.index)
        #print(f"RAW PRICES:\n {raw_prices}")
        df['time'] = df['time'].astype(str)
        df['time'] = df['time'].str.replace(r' \+0$', '', regex=True)
        df['time'] = df['time'].str.replace(r':$', '', regex=True)
        df['time'] = pd.to_datetime(df['time'], format="%b %d %Y %H")
        df['time_numeric'] = df['time'].astype('int64') // 10**9
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        df = df.sort_values("time")

        # Create dataframe for extra features
        df['day_of_week'] = df['time'].dt.dayofweek
        df['month'] = df['time'].dt.month
        df['year'] = df['time'].dt.year
        df['day'] = df['time'].dt.day
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['price_rolling_mean_7'] = df['price'].rolling(window=7, min_periods=1).mean()
        df['price_diff'] = df['price'].diff().fillna(0)
        df['volume_rolling_mean_7'] = df['volume'].rolling(window=7, min_periods=1).mean()
        df = df.fillna(0)
        return df

    # Generate hash for dataset
    def _hash_dataset(self, timestamp: int, df: pd.DataFrame):
        buf = io.BytesIO()
        df[self.feature_cols + ["price"]].to_parquet(buf, index=False)
        hash_input = (
            str(self.user_id).encode("utf-8") +
            str(self.item_id).encode("utf-8") +
            str(timestamp).encode("utf-8") +
            buf.getvalue()
        )
        return hashlib.sha256(hash_input).hexdigest()[:16]

    def _train_and_eval_actual(self, raw_prices: str):
        # Normalize
        df = self._normalize_prices(raw_prices)
        X = df[self.feature_cols]
        scaler = StandardScaler()
        X_normalized = scaler.fit_transform(X)
        y = df["price"]

        # Split and create training pipeline
        X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.3, random_state=42)
        pipe = Pipeline([("rf", RandomForestRegressor(
            n_estimators=750, max_depth=20, min_samples_leaf=5, max_features="sqrt",
            bootstrap=True, n_jobs=2, random_state=42))])
        pipe.fit(X_train, y_train)

        # Generate Results and metrics
        test_pred = pipe.predict(X_test)
        mse = float(mean_squared_error(y_test, test_pred))
        r2 = float(r2_score(y_test, test_pred))
        return pipe, scaler, df, {"mse": mse, "r2": r2}

    # Generate training graph to display model performance
    def _generate_training_graph(self, json_obj: str):
        # Load model artifacts and setup dataframe
        if s3_storage_manager.s3_client:
            pipe = s3_storage_manager.download_model_or_scaler(self.model_path)
            scaler = s3_storage_manager.download_model_or_scaler(self.scaler_path)
        else:
            pipe = joblib.load(self.model_path)
            scaler = joblib.load(self.scaler_path)
        df = pd.DataFrame(json_obj)
        df = self._normalize_prices(df)
        X = df[self.feature_cols]
        X_normalized = scaler.transform(X)
        y = df['price']
        pred = pipe.predict(X_normalized)
        df['predicted'] = pred
        df = df.sort_values('time')
        buf = io.BytesIO()

        # Create graph
        plt.figure(figsize=(12, 6))
        plt.plot(df['time'], y, label='Actual Price', marker='o')
        plt.plot(df['time'], pred, label='Predicted Price', marker='x')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.title(f'Actual vs Predicted Price for user {self.username}, item {self.item_name}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return buf.getvalue()

    # Generate prediction graph for a given predicitions
    def _generate_prediction_graph(self, prediction_df: pd.DataFrame):
        buf = io.BytesIO()
        plt.figure(figsize=(12, 6))
        plt.plot(prediction_df['time'], prediction_df['predicted_price'], label='Predicted Price', marker='x')
        plt.xlabel('Time')
        plt.ylabel('Predicted Price')
        plt.title(f'Predicted Price for user {self.username}, item {self.item_name}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return buf.getvalue()
    
    # Save model artifacts locally
    def _save_model_data_local(self, pipe, scaler, feature_means, data_hash):
        try:
            # Ensure directories exist
            print(f"Ensuring directories exist: {self.MODEL_DIR}, {self.SCALER_DIR}, {self.FEATURES_DIR}")
            os.makedirs(self.MODEL_DIR, exist_ok=True)
            os.makedirs(self.SCALER_DIR, exist_ok=True)
            os.makedirs(self.FEATURES_DIR, exist_ok=True)
            print("Directories created successfully")

            # Model
            model_path = os.path.join(self.MODEL_DIR, f"model_{self.user_id}_{self.item_id}_{data_hash}.joblib")
            joblib.dump(pipe, model_path)
            
            # Scaler
            scaler_path = os.path.join(self.SCALER_DIR, f"scaler_{self.user_id}_{self.item_id}_{data_hash}.joblib")
            joblib.dump(scaler, scaler_path)
            
            # Feature stats
            stats_path = os.path.join(self.FEATURES_DIR, f"feature_means_{self.user_id}_{self.item_id}_{data_hash}.json")
            with open(stats_path, 'w') as f:
                json.dump(feature_means, f)
            
            return model_path, scaler_path, stats_path
        except Exception as e:
            raise RuntimeError(f"Failed to save model data locally: {e}")
    
    # Save model artifacts to S3
    def _save_model_data_s3(self, pipe, scaler, feature_means, data_hash):
        try:
            # Model
            model_key = f"models/model_{self.user_id}_{self.item_id}_{data_hash}.joblib"
            s3_storage_manager.upload_model_or_scaler(pipe, model_key)
            
            # Scaler
            scaler_key = f"scalers/scaler_{self.user_id}_{self.item_id}_{data_hash}.joblib"
            s3_storage_manager.upload_model_or_scaler(scaler, scaler_key)

            # Feature stats
            stats_key = f"features/feature_means_{self.user_id}_{self.item_id}_{data_hash}.json"
            s3_storage_manager.upload_json_data(json.dumps(feature_means), stats_key)
            return model_key, scaler_key, stats_key
        except Exception as e:
            raise RuntimeError(f"Failed to save model data to S3: {e}")

    # Create model from raw price data
    def create_model(self, raw_prices: str):
        try:
            df = self._normalize_prices(raw_prices)
            time_stamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            data_hash = self._hash_dataset(time_stamp, df)
            
            pipe, scaler, df, metrics = self._train_and_eval_redis(raw_prices)
            feature_means = {
                "volume": float(df["volume"].mean()),
                "price_rolling_mean_7": float(df["price_rolling_mean_7"].mean()),
                "price_diff": float(df["price_diff"].mean()),
                "volume_rolling_mean_7": float(df["volume_rolling_mean_7"].mean())
            }
            # Setup directories and file paths
            if s3_storage_manager.s3_client:
                model_path, scaler_path, stats_path = self._save_model_data_s3(pipe, scaler, feature_means, data_hash)
            else:
                model_path, scaler_path, stats_path = self._save_model_data_local(pipe, scaler, feature_means, data_hash)
            
            # Set instance variables for later use
            self.model_path = model_path
            self.scaler_path = scaler_path
            self.stats_path = stats_path
            
            # Generate and return the generated graphs
            graph = self._generate_training_graph(raw_prices)
            return {
                "user_id": self.user_id,
                "group_id": self.item_id,
                "data_hash": data_hash,
                "model_path": model_path,
                "scaler_path": scaler_path,
                "stats_path": stats_path,
                "metrics": metrics,
                "graph": graph
            }
        except Exception as e:
            raise RuntimeError(f"Error in create_model: {e}")

    # Generate a prediction given a time range
    def generate_prediction(self, start_time: str, end_time: str, model_path: str = None, scaler_path: str = None, stats_path: str = None):
        try:
            # Load model artifacts
            if s3_storage_manager.s3_client:
                pipe = s3_storage_manager.download_model_or_scaler(model_path)
                scaler = s3_storage_manager.download_model_or_scaler(scaler_path)
                feature_means = s3_storage_manager.download_json_data(stats_path)
            else:
                pipe = joblib.load(model_path)
                scaler = joblib.load(scaler_path)
                with open(stats_path, "r") as f:
                    feature_means = json.load(f)

            # Create prediction DataFrame
            times = pd.date_range(start=start_time, end=end_time, freq='D')
            X_pred = pd.DataFrame({
                "time_numeric": times.astype('int64') // 10**9,
                "volume": np.full(len(times), feature_means["volume"]),
                "day_of_week": times.dayofweek,
                "month": times.month,
                "year": times.year,
                "day": times.day,
                "is_weekend": np.isin(times.dayofweek, [5, 6]).astype(int),
                "price_rolling_mean_7": np.full(len(times), feature_means["price_rolling_mean_7"]),
                "price_diff": np.full(len(times), feature_means["price_diff"]),
                "volume_rolling_mean_7": np.full(len(times), feature_means["volume_rolling_mean_7"])
            })

            # Normalize and make a prediction from the model
            X_pred_scaled = scaler.transform(X_pred)
            predicted_prices = pipe.predict(X_pred_scaled)
            result = pd.DataFrame({
                "time": times,
                "predicted_price": predicted_prices
            })
            # Generate and return the prediction graph
            graph = self._generate_prediction_graph(result)
            return { "result": result, "graph": graph }
        except Exception as e:
            raise RuntimeError(f"Error in generate_prediction: {e}")