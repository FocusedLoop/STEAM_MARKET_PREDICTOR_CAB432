import requests, jwt, os

from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError

from app.models.models_users import model_get_or_create_user_profile


COGNITO_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.environ.get("COGNITO_APP_CLIENT_ID")

COGNITO_ISSUER = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
)
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

jwks = requests.get(JWKS_URL).json()["keys"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes and validates the Cognito JWT using the PyJWT library.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}

        for key in jwks:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise credentials_exception

        public_key = RSAAlgorithm.from_jwk(rsa_key)

        payload = jwt.decode(
            token,
            public_key,  # type: ignore[arg-type]
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER,
        )

        # Extract Cognito user ID, username, and steam_id from payload
        cognito_id = payload.get("sub")
        username = payload.get("cognito:username") or payload.get("username")
        steam_id = payload.get("custom:steam_id")
        
        if not cognito_id or not username:
            raise credentials_exception
        
        try:
            db_user = model_get_or_create_user_profile(cognito_id, username, steam_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        
        # Return combined payload with database user_id
        # print("DB USER:", db_user)
        # print("PAYLOAD:", payload)
        # print("COGNITO ID:", cognito_id)
        # print("USERNAME:", username)
        # print("STEAM ID:", steam_id)
        # print("USER ID:", db_user["user_id"])
        # print("COGNITO USERNAME:", db_user["username"])
        return {
            **payload,
            "user_id": db_user["user_id"],
            "username": db_user["username"],
            "cognito_id": cognito_id,
            "steam_id": db_user["steam_id"]
        }

    except PyJWTError:
        raise credentials_exception
