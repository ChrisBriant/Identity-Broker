import jwt
import os
from jwt.exceptions import ExpiredSignatureError, InvalidAudienceError, InvalidSignatureError
from datetime import datetime, timedelta, timezone
from functools import wraps
from fastapi import HTTPException, Header, Request
from typing import Optional

# Settings for JWT
#SECRET_KEY = os.environ.get("SECRET_KEY")  # Use a secure key from your Django settings
ALGORITHM = "HS256"             # Use HS256 or any preferred algorithm
ACCESS_TOKEN_LIFETIME = 60      # Token lifetime in seconds
REFRESH_TOKEN_LIFETIME = 120
REFRESH_TOKEN_LIFETIME_HOURS=2
REFRESH_TOKEN_LIFETIME_DAYS=30
#AUTH_KEY_CHECK = os.environ.get("AUTH_KEY")

# GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
# GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

#Custom exceptions

class RefreshTokenExpiredError(Exception):
    """Raised when the refresh token has expired."""
    pass


class InvalidRefreshTokenError(Exception):
    """Raised when the refresh token is invalid."""
    pass

    
def obtain_jwt_token(user_id,external_id,idp,alias):
    # Generate a JWT token
    payload = {
        "user_id": user_id,
        #"external_id" : external_id, #Omit for security?
        "alias" : alias,
        "idp" : idp,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_LIFETIME),
    }
    jwt_token = jwt.encode(payload, os.environ.get("SECRET_KEY"), algorithm=ALGORITHM)

    return jwt_token


def obtain_jwt_pair(user_id, idp, alias):
    # 1. Generate Access Token (Short-lived)
    access_payload = {
        "user_id": user_id,
        "alias": alias,
        "idp": idp,
        "type": "access",  # Important to distinguish types
        "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_LIFETIME),
    }
    access_token = jwt.encode(access_payload, os.environ.get("SECRET_KEY"), algorithm=ALGORITHM)
    print("ACCESS EXPIRES", access_payload["exp"])

    # 2. Generate Refresh Token (Long-lived)
    refresh_payload = {
        "user_id": user_id,
        "alias": alias,
        "idp": idp,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_LIFETIME),
    }
    refresh_token = jwt.encode(refresh_payload, os.environ.get("SECRET_KEY"), algorithm=ALGORITHM)
    print("REFRESH EXPIRES", refresh_payload["exp"])

    return {
        "access": access_token,
        "refresh": refresh_token
    }
    
def refresh_jwt_pair(refresh_token: str):
    print("REFRESH TOKEN", refresh_token)
    try:
        payload = jwt.decode(
            refresh_token,
            os.environ.get("SECRET_KEY"),
            algorithms=[ALGORITHM]
        )

        print("JWT PAYLOAD")

        # Ensure this is a refresh token
        if payload.get("type") != "refresh":
            raise Exception("Invalid token type")

        user_id = payload.get("user_id")

        # If you stored these in the refresh token (recommended)
        alias = payload.get("alias")
        idp = payload.get("idp")

        # Generate new tokens
        return obtain_jwt_pair(user_id, idp, alias)

    except jwt.ExpiredSignatureError:
        raise RefreshTokenExpiredError("Refresh token expired")

    except jwt.InvalidTokenError:
        raise InvalidRefreshTokenError("Invalid refresh token")
    

async def validate_jwt_token(Authorization : str = Header()):
  if not Authorization or not Authorization.startswith('Bearer '):
      raise HTTPException(status_code=401, detail="Authorization header missing or invalid.")
  
  # Extract the Authorization
  Authorization = Authorization.split(' ')[1]
  
  try:
      # Decode and verify the Authorization
      payload = jwt.decode(Authorization, os.environ.get("SECRET_KEY"), algorithms=[ALGORITHM])
  except ExpiredSignatureError:
      raise HTTPException(status_code=401, detail="Token has expired.")
  except InvalidAudienceError:
      raise HTTPException(status_code=401, detail="Invalid audience.")
  except InvalidSignatureError:
      raise HTTPException(status_code=401, detail="Invalid token signature.")
  except Exception:
      raise HTTPException(status_code=401, detail="Invalid token.")
  return payload


async def validate_jwt_cookie(request: Request):
    
    token = request.cookies.get("access_token")
    print("TRYING TO VALIDATE THE COOKIE", token)
    
    if not token:
        raise HTTPException(status_code=401, detail="Authentication cookie missing.")

    try:
        payload = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience.")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return payload


async def validate_jwt(request: Request):

    token = None

    # 1. Try Authorization header (mobile/API clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. Fallback to cookie (browser clients)
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication token missing.")

    try:
        payload = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Invalid audience.")
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

    return payload