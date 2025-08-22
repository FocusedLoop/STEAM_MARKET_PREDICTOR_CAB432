from fastapi import APIRouter
from app.controllers.controllers_users import login, sign_up

router = APIRouter()

router.post("/login", response_model=dict)(login)

router.post("/sign-up", response_model=dict)(sign_up)
