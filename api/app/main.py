from fastapi import FastAPI
from dotenv import load_dotenv
from .aws_values import load_parameters
import uvicorn, os

load_dotenv()
os.environ.update(load_parameters())

from app.routes import router_items, router_users, router_steam

# Initialize APIno
SITE_PORT = os.environ.get("SITE_PORT")

app = FastAPI(
    title="Steam Market Price Predictor API",
    description="API for predicting Steam market item prices",
    version="1.0.0",
)

# Prefix is used to group routes under a common path
app.include_router(router_items, prefix="/group")
app.include_router(router_steam, prefix="/steam")
app.include_router(router_users, prefix="/users")

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=SITE_PORT)