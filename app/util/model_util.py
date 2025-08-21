import pandas as pd
import numpy as np
import hashlib
import io
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score

# Normalize data
def normalize_prices(raw_prices):
    df = pd.DataFrame(raw_prices, columns=["time", "price", "volume"])
    df["time"] = (df["time"].str.replace(r' \+0$', '', regex=True)
                           .str.replace(r':$', '', regex=True))
    df["time"] = pd.to_datetime(df["time"])
    df["time_numeric"] = df["time"].view("int64") // 10**9
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    df = df.sort_values("time")
    return df

# Create dataset hash
def hash_dataset(df: pd.DataFrame) -> str:
    buf = io.BytesIO()
    df[["time_numeric", "volume", "price"]].to_parquet(buf, index=False)
    return hashlib.sha256(buf.getvalue()).hexdigest()[:12]

# Train and evaluate model
def train_and_eval(raw_prices):
    df = normalize_prices(raw_prices)
    X = df[["time_numeric", "volume"]]
    y = df["price"]
    split_idx = int(len(df)*0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    pipe = Pipeline([("rf", RandomForestRegressor(n_estimators=300, max_depth=14, min_samples_leaf=5, max_features="sqrt", bootstrap=True, n_jobs=-1, random_state=42))])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    mse = float(mean_squared_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))
    return pipe, df, {"mse": mse, "r2": r2}, hash_dataset(df)


# USE AWS_BUCKET TO SAVE MODELS