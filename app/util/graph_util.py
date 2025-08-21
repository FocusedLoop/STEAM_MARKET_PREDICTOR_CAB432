import matplotlib.pyplot as plt
import pandas as pd
import pickle
import os

# TODO - MAKE WORK WITH AWS BUCKETS?
def generate_graph(user_id, item_id, model_path, scaler_path, json_obj, output_dir="plots"):
    """
    Loads the model and scaler, predicts prices for the given item, and plots actual vs predicted.
    Assumes json_obj is a list of dicts filtered for the specific user_id and item_id.
    Saves the plot to output_dir and returns the file path.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

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

    # Sort by time for a clean plot
    df['predicted'] = pred
    df = df.sort_values('time')

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], y, label='Actual Price', marker='o')
    plt.plot(df['time'], pred, label='Predicted Price', marker='x')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title(f'Actual vs Predicted Price for user {user_id}, item {item_id}')
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"price_prediction_{user_id}_{item_id}.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Graph saved to {plot_path}")
    return plot_path