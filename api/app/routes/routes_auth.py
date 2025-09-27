from fastapi import APIRouter, status
from app.controllers.controller_auth import (
    UserCreate,
    UserLogin,
    UserConfirm,
    TokenRequest,
    MfaChallenge,
    register_user,
    login_user,
    confirm_user,
    exchange_code_for_tokens,
    respond_to_mfa_challenge
)
from pydantic import BaseModel

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    """
    Endpoint to register a new user in Cognito.
    """
    register_user(user)
    return {
        "message": "User created successfully. Please check your email to verify your account."
    }


@router.post("/confirm", status_code=status.HTTP_200_OK)
def confirm_new_user(user: UserConfirm):
    """
    Endpoint to confirm a user's account with a code from their email.
    """
    confirm_user(user)
    return {"message": "Your account has been successfully verified and you can now log in."}


@router.post("/login")
def user_login(user: UserLogin):
    """
    Endpoint to log in a user.
    Returns either JWTs on success, or an MFA challenge if required.
    """
    tokens_or_challenge = login_user(user)

    if "IdToken" in tokens_or_challenge:
        return {
            "id_token": tokens_or_challenge["IdToken"],
            "access_token": tokens_or_challenge["AccessToken"],
            "refresh_token": tokens_or_challenge["RefreshToken"],
        }
    else:
        return tokens_or_challenge

@router.post("/mfa-challenge")
def submit_mfa_challenge(challenge: MfaChallenge):
    """
    Endpoint for the second step of MFA login.
    """
    return respond_to_mfa_challenge(challenge)

@router.post("/token")
def get_token(request: TokenRequest):
    """
    Endpoint to exchange an authorization code for tokens.
    """
    return exchange_code_for_tokens(request.code, request.redirect_uri)
