from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routes import router_items, router_users
import os

SITE_PORT = os.environ.get("SITE_PORT")

app = FastAPI(
    title="Task Management API",
    description="API for managing tasks",
    version="0.0.1",
)

# Prefix is used to group routes under a common path
app.include_router(router_items, prefix="/tasks")
app.include_router(router_users, prefix="/users")

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=SITE_PORT)