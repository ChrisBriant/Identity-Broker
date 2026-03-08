import os
import requests
from fastapi import HTTPException
from .base_provider import BaseProvider
from urllib.parse import urlencode


class GoogleProvider(BaseProvider):

    async def get_auth_url(self):
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"

        params = {
            "client_id": os.environ.get("CLIENT_ID_GL"),
            "redirect_uri": os.environ.get("CLIENT_REDIRECT_URI"),
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }

        return f"{base_url}?{urlencode(params)}"

    async def exchange_code(self, code: str):

        url = "https://oauth2.googleapis.com/token"

        payload = {
            "client_id": os.environ.get("CLIENT_ID_GL"),
            "client_secret": os.environ.get("CLIENT_SECRET_GL"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": os.environ.get("CLIENT_REDIRECT_URI")
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print("RESPONSE", response.text, response.status_code)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed obtaining Google token"
            )

        return response.json()["access_token"]
    
    async def get_user_info(self, access_token: str):
        url = "https://www.googleapis.com/oauth2/v2/userinfo"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed obtaining Google profile"
            )

        return response.json()
    
