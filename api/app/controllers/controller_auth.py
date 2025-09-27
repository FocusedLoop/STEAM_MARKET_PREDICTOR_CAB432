import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr

import requests
import os
import hmac
import hashlib
import base64

COGNITO_REGION = os.environ.get("COGNITO_REGION")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")
COGNITO_APP_CLIENT_SECRET = os.environ.get("COGNITO_APP_CLIENT_SECRET")
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN")

cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)



class UserCreate(BaseModel):
    username: str          
    email: EmailStr
    password: str
    steam_id: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserConfirm(BaseModel):
    username: str     
    confirmation_code: str


class TokenRequest(BaseModel):
    code: str
    redirect_uri: str


class MfaChallenge(BaseModel):
    username: str      
    mfa_code: str
    session: str



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


def respond_to_mfa_challenge(challenge: MfaChallenge):
    """
    Submits the MFA code and session to Cognito to complete authentication.
    This version handles the EMAIL_OTP custom challenge.
    """
    try:
        secret_hash = get_secret_hash(challenge.username)
        
        challenge_responses = {
            "USERNAME": challenge.username,
            "EMAIL_OTP_CODE": challenge.mfa_code,
        }

        if secret_hash:
            challenge_responses["SECRET_HASH"] = secret_hash

        response = cognito_client.respond_to_auth_challenge(
            ClientId=COGNITO_APP_CLIENT_ID,
            ChallengeName='EMAIL_OTP',
            Session=challenge.session,
            ChallengeResponses=challenge_responses
        )

        if "AuthenticationResult" in response:
            return response["AuthenticationResult"]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code or unexpected challenge."
            )
            
    except ClientError as e:
        if e.response["Error"]["Code"] in ["CodeMismatchException", "NotAuthorizedException"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def exchange_code_for_tokens(code: str, redirect_uri: str):
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    auth_str = f"{COGNITO_APP_CLIENT_ID}:{COGNITO_APP_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    payload = {
        "grant_type": "authorization_code", "client_id": COGNITO_APP_CLIENT_ID,
        "code": code, "redirect_uri": redirect_uri,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {b64_auth_str}",
    }
    try:
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = "Failed to exchange authorization code for tokens."
        if e.response is not None: error_detail += f" Details: {e.response.text}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)


def register_user(user: UserCreate):
    """
    Registers a new user in the Cognito User Pool with a username and email.
    """
    try:
        params = {
            'ClientId': COGNITO_APP_CLIENT_ID,
            'Username': user.username, 
            'Password': user.password,
            'UserAttributes': [
                {"Name": "email", "Value": user.email},
                {"Name": "custom:steam_id", "Value": user.steam_id}
            ]
        }
        
        secret_hash = get_secret_hash(user.username) 
        
        if secret_hash:
            params['SecretHash'] = secret_hash

        response = cognito_client.sign_up(**params)
        return response
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UsernameExistsException":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This username is already taken.")
        elif error_code == "InvalidParameterException":
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parameter provided. Check password policy or attributes.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")


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
    Authenticates a user via username and password.
    Note: Cognito will allow email login if email is an alias.
    """
    try:
        auth_params = {
            "USERNAME": user.username,
            "PASSWORD": user.password
        }

        secret_hash = get_secret_hash(user.username)

        if secret_hash:
            auth_params["SECRET_HASH"] = secret_hash

        response = cognito_client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_params,
        )

        if "AuthenticationResult" in response:
            return response["AuthenticationResult"]
        elif "ChallengeName" in response:
            if response["ChallengeName"] in ["SOFTWARE_TOKEN_MFA", "SMS_MFA", "CUSTOM_CHALLENGE", "EMAIL_OTP"]:
                return {
                    "challengeName": "MFA_CHALLENGE",
                    "session": response["Session"],
                    "username": user.username 
                }
            elif response["ChallengeName"] == "NEW_PASSWORD_REQUIRED":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must set a new password.")
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unhandled Cognito challenge: {response['ChallengeName']}")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected response from Cognito.")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ["NotAuthorizedException", "UserNotFoundException"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password.")
        elif error_code == "UserNotConfirmedException":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not confirmed. Please check your email for a verification code.")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
