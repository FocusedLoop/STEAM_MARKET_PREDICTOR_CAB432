from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils_ml import PriceModel, validate_price_history
import os, uvicorn, logging, base64

app = FastAPI(title="ML Service", version="1.0.0")
PORT = os.getenv("ML_PORT")

# Logging
LOG_FILE = os.environ.get("ML_LOG_FILE", "/tmp/ml_service.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Models
class TrainRequest(BaseModel):
    user_id: int
    username: str
    item_id: int
    item_name: str
    price_history: dict

class PredictRequest(BaseModel):
    user_id: int
    username: str
    item_id: int
    item_name: str
    start_time: str
    end_time: str
    data_hash: str


class MLResponse(BaseModel):
    success: bool
    message: str
    data: dict = None

# Endpoints
@app.post("/train", response_model=MLResponse)
async def train_model(request: TrainRequest):
    """Train a model"""
    try:
        model = PriceModel(request.user_id, request.username, request.item_id, request.item_name)
        logging.info(f"Training model for item {request.item_name} (ID: {request.item_id}) of user {request.username} (ID: {request.user_id})")
        raw_prices = request.price_history.get("prices")
        logging.info(f"Price history raw_prices: \n===========\n{raw_prices}\n===========")
        result = model.create_model(raw_prices)

        #logging.info(f"Training result: {result}")
        if isinstance(result.get("graph"), bytes):
            result["graph"] = base64.b64encode(result["graph"]).decode("utf-8")
        return MLResponse(
            success=True,
            message="Model trained successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=MLResponse)
async def predict_price(request: PredictRequest):
    """Make prediction"""
    try:
        model = PriceModel(request.user_id, request.username, request.item_id, request.item_name)
        result = model.generate_prediction(request.start_time, request.end_time, request.data_hash)
        #logging.info(f"Prediction result: {result}")

        if isinstance(result.get("graph"), bytes):
            result["graph"] = base64.b64encode(result["graph"]).decode("utf-8")
        return MLResponse(
            success=True,
            message="Prediction completed",
            data=result
        )
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", response_model=MLResponse)
async def validate_price_history_endpoint(price_history: dict):
    """Validate price history data format"""
    try:
        is_valid, message = validate_price_history(price_history)
        logger.info(f"Validation result: valid={is_valid}, message='{message}'")
        return MLResponse(
            success=True,
            message="Price history validation completed",
            data={"valid": is_valid, "error": message}
        )
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    logging.info(f"Starting ML service on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)