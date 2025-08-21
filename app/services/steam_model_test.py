from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
#from sklearn.datasets import make_regression
import pandas as pd
import time

# REPLACE WITH MONGODB
df = pd.read_json("price_history_raw.json")
df[['time', 'price', 'volume']] = pd.DataFrame(df['prices'].tolist(), index=df.index) # Create frames

# Clean Time Field and convert to datetime
df['time'] = df['time'].str.replace(r' \+0$', '', regex=True)  # Remove ' +0'
df['time'] = df['time'].str.replace(r':$', '', regex=True)     # Remove trailing colon
df['time'] = pd.to_datetime(df['time'])
df['time_numeric'] = df['time'].astype('int64') // 10**9

print(df[['time', 'time_numeric', 'volume', 'price']].head())


# Set X and Y values
X = df[['time_numeric', 'volume']]
y = df['price']

print(X.head())
print(y.head())

# # Normalize
scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)

# Create train and test split
X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.3, random_state=42)

# Predict
rf = RandomForestRegressor(
    n_estimators=300,
    max_depth=14,
    min_samples_leaf=5, 
    max_features="sqrt",
    bootstrap=True,
    n_jobs=4,
    random_state=42
)

rf = rf.fit(X_train, y_train)
test_pred =rf.predict(X_test)
train_pred = rf.predict(X_train)

# Get the test indices and corresponding times
test_indices = y_test.index
time_test = df.loc[test_indices, 'time']

# Convert everything to a DataFrame for easy sorting
plot_df = pd.DataFrame({
    'time': time_test,
    'actual': y_test,
    'predicted': test_pred
})

# Sort by time
plot_df = plot_df.sort_values('time')

# Plot
plt.figure(figsize=(12, 6))
plt.plot(plot_df['time'], plot_df['actual'], label='Actual Price', marker='o')
plt.plot(plot_df['time'], plot_df['predicted'], label='Predicted Price', marker='x')
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Actual vs Predicted Price Over Time')
plt.legend()
plt.tight_layout()
plt.savefig("price_prediction_plot.png")
plt.close()

# Print regression summary
mse = mean_squared_error(y_test, test_pred)
r2 = r2_score(y_test, test_pred)
print(f"RandomForestRegressor Test MSE: {mse:.4f}")
print(f"RandomForestRegressor Test R^2: {r2:.4f}")
time.sleep(0.5)

# BRAIN STORMING
# https://chatgpt.com/c/68a460f7-36ec-8322-b1e8-28ba5b015779
# https://github.com/Frid0l1n/Random-Forest/blob/main/rewrite/random_forest.py 

# IMAGE URL 
# https://community.akamai.steamstatic.com/economy/image/<icon_url>

import pickle

# Create a model from the json object, generates a model and saves to a pkl file
def create_model(json_obj: list[dict], model_path="model.pkl", scaler_path="scaler.pkl"):
    """
    Takes a JSON object (list of dicts), trains a RandomForestRegressor,
    and saves the trained model and scaler to disk.
    """
    df = pd.DataFrame(json_obj)
    if 'prices' in df.columns:
        df[['time', 'price', 'volume']] = pd.DataFrame(df['prices'].tolist(), index=df.index)
    df['time'] = df['time'].str.replace(r' \+0$', '', regex=True)
    df['time'] = df['time'].str.replace(r':$', '', regex=True)
    df['time'] = pd.to_datetime(df['time'])
    df['time_numeric'] = df['time'].astype('int64') // 10**9

    X = df[['time_numeric', 'volume']]
    y = df['price']

    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_normalized, y, test_size=0.3, random_state=42)

    rf = RandomForestRegressor(
        n_estimators=300,
        max_depth=14,
        min_samples_leaf=5, 
        max_features="sqrt",
        bootstrap=True,
        n_jobs=4,
        random_state=42
    )
    rf.fit(X_train, y_train)

    # Save model and scaler
    with open(model_path, "wb") as f:
        pickle.dump(rf, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"Model saved to {model_path}, scaler saved to {scaler_path}")

    return rf, scaler

# Creates a graph given a user_id and specific item_id, uses these to find the right pkl file
def generate_graph(user_id, item_id, model_path="model.pkl", scaler_path="scaler.pkl", json_obj=None):
    """
    Loads the model and scaler, predicts prices for the given item, and plots actual vs predicted.
    Assumes json_obj is a list of dicts filtered for the specific user_id and item_id.
    """

    # Load model and scaler
    with open(model_path, "rb") as f:
        rf = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    # Prepare data
    df = pd.DataFrame(json_obj)
    if 'prices' in df.columns:
        df[['time', 'price', 'volume']] = pd.DataFrame(df['prices'].tolist(), index=df.index)
    df['time'] = df['time'].str.replace(r' \+0$', '', regex=True)
    df['time'] = df['time'].str.replace(r':$', '', regex=True)
    df['time'] = pd.to_datetime(df['time'])
    df['time_numeric'] = df['time'].astype('int64') // 10**9

    X = df[['time_numeric', 'volume']]
    y = df['price']

    X_normalized = scaler.transform(X)
    pred = rf.predict(X_normalized)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], y, label='Actual Price', marker='o')
    plt.plot(df['time'], pred, label='Predicted Price', marker='x')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title(f'Actual vs Predicted Price for user {user_id}, item {item_id}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"price_prediction_{user_id}_{item_id}.png")
    plt.close()
    print(f"Graph saved to price_prediction_{user_id}_{item_id}.png")