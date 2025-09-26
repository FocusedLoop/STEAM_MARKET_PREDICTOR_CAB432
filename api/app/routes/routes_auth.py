from fastapi import APIRouter, status
from app.controllers.controller_auth import (
    UserCreate,
    UserLogin,
    UserConfirm,
    register_user,
    login_user,
    confirm_user,
)

router = APIRouter()


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    """
    Endpoint to register a new user in Cognito.
    """
    register_user(user)
    return {
        "message": "User created successfully. Please check your email to verify your account."
    }


@router.post("/auth/confirm", status_code=status.HTTP_200_OK)
def confirm_new_user(user: UserConfirm):
    """
    Endpoint to confirm a user's account with a code from their email.
    """
    confirm_user(user)
    return {"message": "Your account has been successfully verified and you can now log in."}


@router.post("/auth/login")
def user_login(user: UserLogin):
    """
    Endpoint to log in a user and retrieve JWTs.
    """
    tokens = login_user(user)
    return {
        "id_token": tokens["IdToken"],
        "access_token": tokens["AccessToken"],
        "refresh_token": tokens["RefreshToken"],
    }
