from fastapi import APIRouter
from app.controllers.controllers_users import login, sign_up

router = APIRouter()

# POST /login
# Takes: JSON body with 'username' and 'password'
# Returns: dict with 'authToken' if successful, 401 error if unauthorized
router.post("/login", response_model=dict)(login)

# POST /sign-up
# Takes: JSON body with 'username', 'password', and 'steam_id'
# Returns: dict with 'authToken' if successful, 400 error if user exists or missing fields
router.post("/sign-up", response_model=dict)(sign_up)