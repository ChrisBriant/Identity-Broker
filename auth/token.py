import jwt
import os
from jwt.exceptions import ExpiredSignatureError, InvalidAudienceError, InvalidSignatureError
from datetime import datetime, timedelta, timezone
from functools import wraps
from fastapi import HTTPException, Header
from typing import Optional

# Settings for JWT
#SECRET_KEY = os.environ.get("SECRET_KEY")  # Use a secure key from your Django settings
ALGORITHM = "HS256"             # Use HS256 or any preferred algorithm
ACCESS_TOKEN_LIFETIME = 120      # Token lifetime in minutes
REFRESH_TOKEN_LIFETIME_DAYS=30
#AUTH_KEY_CHECK = os.environ.get("AUTH_KEY")

# GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
# GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')

    
def obtain_jwt_token(user_id,external_id,idp,alias):
    # Generate a JWT token
    payload = {
        "user_id": user_id,
        #"external_id" : external_id, #Omit for security?
        "alias" : alias,
        "idp" : idp,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME),
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
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME),
    }
    access_token = jwt.encode(access_payload, os.environ.get("SECRET_KEY"), algorithm=ALGORITHM)

    # 2. Generate Refresh Token (Long-lived)
    refresh_payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS),
    }
    refresh_token = jwt.encode(refresh_payload, os.environ.get("SECRET_KEY"), algorithm=ALGORITHM)

    return {
        "access": access_token,
        "refresh": refresh_token
    }
    
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
