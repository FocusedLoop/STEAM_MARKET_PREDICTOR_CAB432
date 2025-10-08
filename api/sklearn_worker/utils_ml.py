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
from queue import Queue, Full
from shared import S3StorageManager
import os, json, threading
from distutils.util import strtobool 

# Limit concurrent trainings
MAX_CONCURRENT_TRAININGS = 2
training_semaphore = threading.Semaphore(MAX_CONCURRENT_TRAININGS)

# Global S3 storage manager instance
s3_storage_manager = S3StorageManager()

LOCAL_STORAGE = bool(strtobool(os.environ.get("LOCAL_STORAGE", "False")))

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

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    QUEUE_STATUS_PATH = os.path.join(BASE_DIR, "tmp/queue_status.txt")
    MODEL_DIR = os.path.join(BASE_DIR, "tmp/models/")
    SCALER_DIR = os.path.join(BASE_DIR, "tmp/scalers/")
    FEATURES_DIR = os.path.join(BASE_DIR, "tmp/features/")
    GRAPH_DIR = os.path.join(BASE_DIR, "tmp/graphs/")
    FEATURE_COLS = [
        "time_numeric", "volume", "day_of_week", "month", "year", "day",
        "is_weekend", "price_rolling_mean_7", "price_diff", "volume_rolling_mean_7"
    ]

    # Shared queue for all training instances among users
    shared_queue = Queue(maxsize=20)
    _worker_started = False

    def __init__(self, user_id: int, username: str, item_id: int, item_name: str):
        self.user_id = user_id
        self.username = username
        self.item_id = item_id
        self.item_name = item_name

    # Get a snapshot of the queue contents
    @classmethod
    def write_queue_status(cls):
        items = list(cls.shared_queue.queue)
        with open(cls.QUEUE_STATUS_PATH, "w") as f:
            f.write("\n")
            f.write("="*30 + "\n")
            f.write("   PriceModel Training Queue\n")
            f.write("="*30 + "\n")
            if not items:
                f.write("Queue is empty.\n")
            else:
                for idx, job in enumerate(items, 1):
                    desc = job.get("func", None)
                    if desc:
                        desc = desc.__name__
                    else:
                        desc = str(job)
                    f.write(f"{idx}. Job: {desc}\n")
            f.write("="*30 + "\n")
            f.write(f"Total jobs in queue: {len(items)}\n")
            f.write("="*30 + "\n")

    # Start the background worker
    @classmethod
    def _start_worker(cls):
        if not cls._worker_started:
            t = threading.Thread(target=cls._queue_worker, daemon=True)
            t.start()
            cls._worker_started = True

    # Background worker for processing jobs
    @classmethod
    def _queue_worker(cls):
        while True:
            job = cls.shared_queue.get()
            if job is None:
                break
            try:
                result = job["func"](*job["args"], **job["kwargs"])
                job["result_queue"].put(result)
            except Exception as e:
                job["result_queue"].put(e)
            finally:
                cls.shared_queue.task_done()

    # Add training job to the queue
    def _train_and_eval(self, raw_prices: str):
        acquired = training_semaphore.acquire(blocking=False)
        if not acquired:
            raise RuntimeError("Server is busy. Please try again later.")

        try:
            self._start_worker()
            result_queue = Queue()
            try:
                PriceModel.shared_queue.put({
                    "func": PriceModel._train_and_eval_actual,
                    "args": (self, raw_prices),
                    "kwargs": {},
                    "result_queue": result_queue
                }, block=False)
            except Full:
                raise RuntimeError("Training queue is full. Please try again later.")
            PriceModel.write_queue_status()
            result = result_queue.get()
            if isinstance(result, Exception):
                raise result
            return result
        finally:
            training_semaphore.release()
    
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
    @staticmethod
    def _hash_dataset(user_id: int, item_id: int, timestamp: int, df: pd.DataFrame):
        buf = io.BytesIO()
        df[PriceModel.FEATURE_COLS + ["price"]].to_parquet(buf, index=False)
        hash_input = (
            str(user_id).encode("utf-8") +
            str(item_id).encode("utf-8") +
            str(timestamp).encode("utf-8") +
            buf.getvalue()
        )
        return hashlib.sha256(hash_input).hexdigest()[:16]

    @staticmethod
    def _train_and_eval_actual(self, raw_prices: str):
        # Normalize
        df = self._normalize_prices(raw_prices)
        X = df[PriceModel.FEATURE_COLS]
        scaler = StandardScaler()
        X_normalized = scaler.fit_transform(X)
        y = df["price"]

        # Split and create training pipeline
        X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.3, random_state=42)
        pipe = Pipeline([("rf", RandomForestRegressor(
            n_estimators=600, max_depth=20, min_samples_leaf=5, max_features="sqrt",
            bootstrap=True, n_jobs=1, random_state=42))])
        pipe.fit(X_train, y_train)

        # Generate Results and metrics
        test_pred = pipe.predict(X_test)
        mse = float(mean_squared_error(y_test, test_pred))
        r2 = float(r2_score(y_test, test_pred))
        return pipe, scaler, df, {"mse": mse, "r2": r2}

    # Generate training graph to display model performance
    def _generate_training_graph(self, json_obj: str, pipe, scaler):
        df = pd.DataFrame(json_obj)
        df = self._normalize_prices(df)
        X = df[PriceModel.FEATURE_COLS]
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

    # Generate prediction graph for a given predictions
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
    def _save_model_data_local(self, pipe, scaler, feature_means, graph, data_hash):
        try:
            # Ensure directories exist
            print(f"Ensuring directories exist: {self.MODEL_DIR}, {self.SCALER_DIR}, {self.FEATURES_DIR}")
            os.makedirs(self.MODEL_DIR, exist_ok=True)
            os.makedirs(self.SCALER_DIR, exist_ok=True)
            os.makedirs(self.FEATURES_DIR, exist_ok=True)
            print("Directories created successfully")

            # Model
            model_key = os.path.join(self.MODEL_DIR, f"model_{data_hash}.joblib")
            joblib.dump(pipe, model_key)
            
            # Scaler
            scaler_key = os.path.join(self.SCALER_DIR, f"scaler_{data_hash}.joblib")
            joblib.dump(scaler, scaler_key)
            
            # Feature stats
            stats_key = os.path.join(self.FEATURES_DIR, f"feature_means_{data_hash}.json")
            with open(stats_key, 'w') as f:
                json.dump(feature_means, f)
            
            # Graph PNG
            graph_key = os.path.join(self.GRAPH_DIR, f"training_graph_{data_hash}.png")
            with open(graph_key, 'wb') as f:
                f.write(graph)
            
            return model_key, scaler_key, stats_key, graph_key, graph_key
        except Exception as e:
            raise RuntimeError(f"Failed to save model data locally: {e}")
    
    # Save model artifacts to S3
    def _save_model_data_s3(self, pipe, scaler, feature_means, graph, data_hash):
        try:
            # Model
            model_key = f"models/model_{data_hash}.joblib"
            s3_storage_manager.upload_file(pipe, model_key, 'model')
            
            # Scaler
            scaler_key = f"scalers/scaler_{data_hash}.joblib"
            s3_storage_manager.upload_file(scaler, scaler_key, 'model')

            # Feature stats
            stats_key = f"features/feature_means_{data_hash}.json"
            s3_storage_manager.upload_file(feature_means, stats_key, 'json')
        
            # Graph PNG
            graph_key = f"graphs/training_graph_{data_hash}.png"
            s3_storage_manager.upload_file(graph, graph_key, 'bytes')
            
            # Generate presigned URL for the graph
            graph_url = s3_storage_manager.generate_download_url(graph_key)
            
            return model_key, scaler_key, stats_key, graph_key, graph_url
        except Exception as e:
            raise RuntimeError(f"Failed to save model data to S3: {e}")

    # Create model from raw price data
    def create_model(self, raw_prices: str):
        try:
            df = self._normalize_prices(raw_prices)
            time_stamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            data_hash = self._hash_dataset(self.user_id, self.item_id, time_stamp, df)
            
            pipe, scaler, df, metrics = self._train_and_eval(raw_prices)
            feature_means = {
                "volume": float(df["volume"].mean()),
                "price_rolling_mean_7": float(df["price_rolling_mean_7"].mean()),
                "price_diff": float(df["price_diff"].mean()),
                "volume_rolling_mean_7": float(df["volume_rolling_mean_7"].mean())
            }

            # Generate and return the generated graphs using the trained pipe and scaler
            graph = self._generate_training_graph(raw_prices, pipe, scaler)

            # Setup directories and file paths
            if LOCAL_STORAGE:
                print("Using local storage to save model artifacts")
                model_path, scaler_path, stats_path, graph_png, graph_url = self._save_model_data_local(pipe, scaler, feature_means, graph, data_hash)
            elif s3_storage_manager.s3_client:
                print("Using S3 to save model artifacts")
                model_path, scaler_path, stats_path, graph_png, graph_url = self._save_model_data_s3(pipe, scaler, feature_means, graph, data_hash)
            else:
                raise RuntimeError("No valid storage method configured for loading model artifacts. Ensure S3 client is available or LOCAL_STORAGE is set.")
            
            # Set instance variables for later use
            self.model_path = model_path
            self.scaler_path = scaler_path
            self.stats_path = stats_path
            self.graph_png = graph_png
            
            return {
                "user_id": self.user_id,
                "group_id": self.item_id,
                "data_hash": data_hash,
                "metrics": metrics,
                "graph": graph,
                "graph_url": graph_url
            }
        except Exception as e:
            raise RuntimeError(f"Error in create_model: {e}")

    # Generate a prediction given a time range
    def generate_prediction(self, start_time: str, end_time: str, data_hash: str):
        try:
            # Reconstruct paths from data_hash
            model_path = f"models/model_{data_hash}.joblib"
            scaler_path = f"scalers/scaler_{data_hash}.joblib"
            stats_path = f"features/feature_means_{data_hash}.json"
            
            # Load model artifacts
            if LOCAL_STORAGE:
                print("Using local storage to save model artifacts")
                pipe = joblib.load(model_path)
                scaler = joblib.load(scaler_path)
                with open(stats_path, "r") as f:
                    feature_means = json.load(f)
            elif s3_storage_manager.s3_client:
                print("Using S3 to load model artifacts")
                pipe = s3_storage_manager.download_file(model_path, 'model')
                scaler = s3_storage_manager.download_file(scaler_path, 'model')
                feature_means = s3_storage_manager.download_file(stats_path, 'json')    
            else:
                raise RuntimeError("No valid storage method configured for loading model artifacts. Ensure S3 client is available or LOCAL_STORAGE is set.")

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

            # Save graph to local or S3
            png_path = f"predictions/prediction_graph_{data_hash}.png"
            if LOCAL_STORAGE:
                os.makedirs(self.GRAPH_DIR, exist_ok=True)
                graph_path = os.path.join(self.GRAPH_DIR, png_path)
                with open(graph_path, "wb") as f:
                    f.write(graph)
                print(f"Prediction graph saved locally at {graph_path}")
                graph_url = graph_path
            elif s3_storage_manager.s3_client:
                graph_key = png_path
                s3_storage_manager.upload_file(graph, graph_key, 'bytes')
                print(f"Prediction graph uploaded to s3://{s3_storage_manager.bucket_name}/{graph_key}")
                graph_url = s3_storage_manager.generate_download_url(graph_key)
            else:
                raise RuntimeError("No valid storage method configured for saving prediction graph. Ensure S3 client is available or LOCAL_STORAGE is set.")
            return { "result": result, "graph": graph, "graph_url": graph_url }
        except Exception as e:
            raise RuntimeError(f"Error in generate_prediction: {e}")
    

# TESTING
if __name__ == "__main__":
    user_id = 1
    item_id = 1
    with open("price_history_raw.json", "r") as f:
        raw_json = json.load(f)
    # Convert list of lists to list of dicts
    raw_prices = [
        {"time": row[0], "price": row[1], "volume": row[2]}
        for row in raw_json["prices"]
    ]
    model = PriceModel(user_id, "testuser", item_id, "testitem")
    model_info = model.create_model(raw_prices)
    #print("Model info:", model_info)

    start_time = "2025-07-14"
    end_time = "2025-10-18"
    prediction = model.generate_prediction(
        start_time,
        end_time
    )
    #print(f"Prediction generated for {start_time} to {end_time} : {prediction}")