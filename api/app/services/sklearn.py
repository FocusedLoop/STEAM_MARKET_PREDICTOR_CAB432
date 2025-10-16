from typing import Dict, Any
import httpx, os, logging

logging.basicConfig(level=logging.INFO)

class SklearnClient:
    """Client to communicate with the sklearn ML service"""
    
    def __init__(self):
        self.base_url = os.getenv("SKLEARN_SERVICE_URL")
        self.timeout = 300.0 #5 minutes
    
    async def train_model(self, user_id: int, username: str, item_id: int, item_name: str, price_history: Dict[str, Any]) -> Dict[str, Any]:
        """Send training request to sklearn service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logging.info(f"Sending training request for item {item_name} (ID: {item_id}) of user {username} (ID: {user_id})")
            logging.info(f"Price history data: \n===========\n{price_history}\n===========")
            response = await client.post(
                f"{self.base_url}/train",
                json={
                    "user_id": user_id,
                    "username": username,
                    "item_id": item_id,
                    "item_name": item_name,
                    "price_history": price_history
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def predict_price(self, user_id: int, username: str, item_id: int, item_name: str, 
                           data_hash: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Send prediction request to sklearn service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/predict",
                json={
                    "user_id": user_id,
                    "username": username,
                    "item_id": item_id,
                    "item_name": item_name,
                    "data_hash": data_hash,
                    "start_time": start_time,
                    "end_time": end_time
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def validate_price_history(self, price_history: Dict[str, Any]) -> bool:
        """Validate price history data format"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logging.info(f"Validating price history data: \n===========\n{price_history}\n===========")
            response = await client.post(f"{self.base_url}/validate", json=price_history)
            response.raise_for_status()
            result = response.json()
            data = result.get("data", {})
            return data.get("valid", False), data.get("error", "")
    
    async def health_check(self) -> bool:
        """Check if sklearn service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False