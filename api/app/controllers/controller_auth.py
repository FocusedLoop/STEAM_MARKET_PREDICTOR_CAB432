import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from pydantic import BaseModel

import os
import hmac
import hashlib
import base64

COGNITO_REGION = os.environ.get("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = os.environ.get("COGNITO_APP_CLIENT_SECRET")

cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)


def get_secret_hash(username: str) -> str | None:
    """Calculates the secret hash for a given username if a client secret is configured."""
    if not COGNITO_APP_CLIENT_SECRET:
        return None

    msg = username + COGNITO_APP_CLIENT_ID
    dig = hmac.new(
        str(COGNITO_APP_CLIENT_SECRET).encode('utf-8'),
        msg=str(msg).encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserConfirm(BaseModel):
    username: str
    confirmation_code: str


def register_user(user: UserCreate):
    """
    Registers a new user in the Cognito User Pool.
    """
    try:
        username_for_cognito = user.username

        params = {
            'ClientId': COGNITO_APP_CLIENT_ID,
            'Username': username_for_cognito,
            'Password': user.password,
            'UserAttributes': [
                {"Name": "email", "Value": user.email},
                {"Name": "preferred_username", "Value": username_for_cognito}
            ]
        }
        
        secret_hash = get_secret_hash(username_for_cognito)
        
        if secret_hash:
            params['SecretHash'] = secret_hash

        response = cognito_client.sign_up(**params)

        return response
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UsernameExistsException":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {e}",
            )

def confirm_user(user: UserConfirm):
    """
    Confirms a new user's account with a confirmation code.
    """
    try:
        secret_hash = get_secret_hash(user.username)
        
        params = {
            'ClientId': COGNITO_APP_CLIENT_ID,
            'Username': user.username,
            'ConfirmationCode': user.confirmation_code,
        }

        if secret_hash:
            params['SecretHash'] = secret_hash
            
        return cognito_client.confirm_sign_up(**params)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["CodeMismatchException", "ExpiredCodeException"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired confirmation code.")
        elif error_code == "UserNotFoundException":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


def login_user(user: UserLogin):
    """
    Authenticates a user and returns JWTs from Cognito.
    """
    try:
        auth_params = {
            "USERNAME": user.email, 
            "PASSWORD": user.password
        }
        secret_hash = get_secret_hash(user.email)
        if secret_hash:
            auth_params["SECRET_HASH"] = secret_hash

        response = cognito_client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_params,
        )
        return response["AuthenticationResult"]
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["NotAuthorizedException", "UserNotFoundException"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        elif error_code == "UserNotConfirmedException":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not confirmed. Please verify your account.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {e}",
            )
