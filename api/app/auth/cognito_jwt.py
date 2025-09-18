import requests
import jwt

from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError


COGNITO_REGION = "ap-southeast-2"
COGNITO_USER_POOL_ID = "ap-southeast-2_INIHjS9fW"
COGNITO_APP_CLIENT_ID = "3j8o6dnhvin7sstr6odsv3o8j8"

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

        return payload

    except PyJWTError:
        raise credentials_exception
