from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils_ml import PriceModel, validate_price_history
import os, uvicorn

app = FastAPI(title="ML Service", version="1.0.0")
PORT = os.getenv("ML_PORT")

# Models
class TrainRequest(BaseModel):
    user_id: int
    username: str
    item_id: int
    item_name: str

class PredictRequest(BaseModel):
    user_id: int
    username: str
    item_id: int
    item_name: str

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
        result = model.create_model()
        
        return MLResponse(
            success=True,
            message="Model trained successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict", response_model=MLResponse)
async def predict_price(request: PredictRequest):
    """Make prediction"""
    try:
        model = PriceModel(request.user_id, request.username, request.item_id, request.item_name)
        result = model.predict()
        
        return MLResponse(
            success=True,
            message="Prediction completed",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", response_model=MLResponse)
async def validate_price_history_endpoint(price_history: dict):
    """Validate price history data format"""
    try:
        is_valid = validate_price_history(price_history)
        return MLResponse(
            success=True,
            message="Price history validation completed",
            data={"valid": is_valid}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)