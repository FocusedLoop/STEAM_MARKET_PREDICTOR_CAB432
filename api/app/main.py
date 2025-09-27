from fastapi import FastAPI
from dotenv import load_dotenv
from .aws_values import load_parameters, load_secret_manager
import uvicorn, os

from app.routes.routes_items import router as items_router
from app.routes.routes_users import router as users_router
from app.routes.routes_steam import router as steam_router
from app.routes.routes_auth import router as auth_router

load_dotenv()
os.environ.update(load_parameters())
os.environ.update(load_secret_manager())

# Initialize APIno
SITE_PORT = os.environ.get("SITE_PORT")

app = FastAPI(
    title="Steam Market Price Predictor API",
    description="API for predicting Steam market item prices",
    version="1.0.0",
)

# Prefix is used to group routes under a common path
app.include_router(items_router, prefix="/group", tags=["Item Groups"])
app.include_router(steam_router, prefix="/steam", tags=["Steam API"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"]) # Authentication routes

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=SITE_PORT)
