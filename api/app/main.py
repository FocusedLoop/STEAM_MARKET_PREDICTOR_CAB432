from fastapi import FastAPI
from dotenv import load_dotenv
from app.aws_values import load_parameters, load_secret_manager
import uvicorn, logging, os

# Configure logging to file and console
LOG_FILE = os.environ.get("LOG_FILE", "/tmp/api.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def configure_environment():
    load_dotenv()
    logger.info("Loading AWS parameters and secrets...")
    os.environ.update(load_parameters())
    os.environ.update(load_secret_manager())

def create_app():
    from app.routes.routes_items import router as items_router
    from app.routes.routes_users import router as users_router
    from app.routes.routes_steam import router as steam_router
    from app.routes.routes_auth import router as auth_router

    app = FastAPI(
        title="Steam Market Price Predictor API",
        description="API for predicting Steam market item prices",
        version="1.0.0",
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(items_router, prefix="/group", tags=["Item Groups"])
    app.include_router(steam_router, prefix="/steam", tags=["Steam API"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

    logger.info("API routes configured successfully")
    return app

configure_environment()
SITE_PORT = int(os.environ.get("APP_PORT", 3010))
logger.info(f"Initializing Steam Market Predictor API on port {SITE_PORT}")
app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting server on host 0.0.0.0 port {SITE_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=SITE_PORT)