from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from providers.provider_registry import get_provider
from data.db_actions import get_or_add_user
from .token import (
    obtain_jwt_token, 
    obtain_jwt_pair, 
    refresh_jwt_pair, 
    validate_jwt_token, 
    validate_jwt_cookie, 
    RefreshTokenExpiredError, 
    InvalidRefreshTokenError,
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME
)
from data.shemas import TokenSchema, ProviderSchema, UserProfileSchema
from typing import List
from pathlib import Path
import json
import os

router = APIRouter()

# Go to project root (adjust parents[n] if needed)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

@router.get("/auth/providers", response_model = List[ProviderSchema])
async def get_providers():

    providers_path = PROJECT_ROOT / "providers" / "providers.json"

    with open(providers_path, "r", encoding="utf-8") as f:
        providers = json.load(f)

    provider_list = [ ProviderSchema(id=p['id'], name=p['name']) for p in providers]
    return provider_list

@router.get("/auth/{provider}/login")
async def login(provider: str):
    try:
        idp = get_provider(provider)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Provider not found"
        )
    except Exception as e:
        #Catch all
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred retrieving the provider {e}"
        ) 
    return {"auth_url": await idp.get_auth_url()}


@router.get("/{provider}/callback", response_model=TokenSchema)
async def auth_callback(provider: str, code: str):

    idp = get_provider(provider)

    access_token = await idp.exchange_code(code)

    #access_token = "MTQ4MDA3NDQ2NTExNDMyOTI5MQ.uv6PGkQHeeSpcUUhAv23WRQwqF4WON"

    user_profile = await idp.get_user_info(access_token)


    # print("DISCORD PROFILE ", user_profile, access_token)

    # user_profile = {
    #     'id': '112023773581453384433', 
    #     'email': 'cbri4nt@gmail.com', 
    #     'verified_email': True, 
    #     'name': 'Chris Briant', 
    #     'given_name': 'Chris', 
    #     'family_name': 'Briant', 
    #     'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIf1fisJjPwLJ6e9uMk_Q46nWohbOwoeP7Gw4b3EwQw0E15fA=s96-c'
    # }

    # print("USER PROFILE RETRIEVED", user_profile)

    # database logic here
    user_record = await get_or_add_user(user_profile["id"],provider,None,user_profile['email'])
    if not user_record:
        raise HTTPException(
            status_code=400,
            detail="Failed to create the user"
        )
    print("USER FROM DATABASE", user_record)
    #Issue a JWT
    jwt_token_pair = obtain_jwt_pair(user_record["id"],user_record["idp"], user_record["alias"]) 
    print("JWT OBTAINED", jwt_token_pair)

    response = TokenSchema(
        access_token = jwt_token_pair['access'],
        refresh_token = jwt_token_pair['refresh'],
    )

    return response

#TEST ROUTE FOR IP INFORMATION
@router.get("/ip-info")
async def ip_info(request: Request):

    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")

    return {
        "ip": ip_address,
        "user_agent": user_agent
    }

@router.get("/{provider}/callbackwithredirect", response_model=TokenSchema)
async def auth_callback_with_redirect(provider: str, code: str):

    idp = get_provider(provider)

    access_token = await idp.exchange_code(code)

    #access_token = "MTQ4MDA3NDQ2NTExNDMyOTI5MQ.uv6PGkQHeeSpcUUhAv23WRQwqF4WON"

    user_profile = await idp.get_user_info(access_token)

    # database logic here
    user_record = await get_or_add_user(user_profile["id"],provider,None,user_profile['email'])
    if not user_record:
        raise HTTPException(
            status_code=400,
            detail="Failed to create the user"
        )
    print("USER FROM DATABASE", user_record)
    #Issue a JWT
    jwt_token_pair = obtain_jwt_pair(user_record["id"],user_record["idp"], user_record["alias"]) 
    print("JWT OBTAINED", jwt_token_pair)

    # response = TokenSchema(
    #     access_token = jwt_token_pair['access'],
    #     refresh_token = jwt_token_pair['refresh'],
    # )

    response = RedirectResponse(
        url=os.environ.get("CLIENT_REDIRECT_URI"),
        status_code=302
    )

    print("RESPONSE OBJECT", os.environ.get("CLIENT_REDIRECT_URI"))

    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token_pair["access"],
        httponly=True,
        secure=True,          # HTTPS only
        samesite="none",
        max_age=ACCESS_TOKEN_LIFETIME,
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=jwt_token_pair["refresh"],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_LIFETIME, 
    )

    return response

@router.get("/session", response_model=UserProfileSchema)
async def get_session(token_data = Depends(validate_jwt_cookie)):
    print("TOKEN DATA", token_data)
    response = UserProfileSchema(
        id=token_data["user_id"],
        idp= token_data["idp"],
        alias=token_data["alias"]
    )
    return response


@router.get("/issuejwt", response_model=TokenSchema)
async def issue_jwt (id: str, idp:str, alias:str):
    jwt_token_pair = obtain_jwt_pair(id,idp,alias)
    response = TokenSchema(
        access_token = jwt_token_pair['access'],
        refresh_token = jwt_token_pair['refresh'],
    )

    return response


@router.get("/issuejwtredirect")
async def issue_jwt_redirect(id: str, idp: str, alias: str):

    jwt_token_pair = obtain_jwt_pair(id, idp, alias)

    response = RedirectResponse(
        url=os.environ.get("CLIENT_REDIRECT_URI"),
        status_code=302
    )

    print("RESPONSE OBJECT", os.environ.get("CLIENT_REDIRECT_URI"))

    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token_pair["access"],
        httponly=True,
        secure=True,          # HTTPS only
        samesite="lax",
        max_age=ACCESS_TOKEN_LIFETIME          
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=jwt_token_pair["refresh"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_LIFETIME  
    )

    return response

@router.get("/refresh", response_model=TokenSchema)
async def refresh_jwt (request:Request):
    refresh_token = request.cookies.get("refresh_token")

    try:
        print("HERE IS THE REFRESH", request.cookies.get("refresh_token"))
        jwt_token_pair = refresh_jwt_pair(refresh_token)
    except RefreshTokenExpiredError as ex_err:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired"
        )
    except InvalidRefreshTokenError as invalid_token_err:
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid"
        )
    except Exception as e:
        print("AN ERROR OCCURRED REFRESHING THE TOKEN", e)
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid"
        )

    response = RedirectResponse(
        url=os.environ.get("CLIENT_REDIRECT_URI"),
        status_code=302
    )

    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token_pair["access"],
        httponly=True,
        secure=True,          # HTTPS only
        samesite="lax",
        max_age=ACCESS_TOKEN_LIFETIME
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=jwt_token_pair["refresh"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_LIFETIME
    )

    return response


@router.post("/refreshtoken", response_model=TokenSchema)
async def refresh_jwt_token (refresh_token:str):
    try:
        jwt_token_pair = refresh_jwt_pair(refresh_token)
    except RefreshTokenExpiredError as ex_err:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired"
        )
    except InvalidRefreshTokenError as invalid_token_err:
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid"
        )
    except Exception as e:
        print("AN ERROR OCCURRED REFRESHING THE TOKEN")
        raise HTTPException(
            status_code=401,
            detail="Refresh token is invalid"
        )
        
    response = TokenSchema(
        access_token = jwt_token_pair['access'],
        refresh_token = jwt_token_pair['refresh'],
    )

    return response

#TODO
#The endpoints with redirect hae been set up, but will need to be consolidated at some point, remove the old architecture
#Set the discord and google providers with the correct redirect code
#Return IDP list with the profile

# EXAMPLE TOKEN FOR TESTING
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMyIsImFsaWFzIjoiTWFyayIsImlkcCI6Imdvb2dsZSIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NzI5NTg0MTB9.YX6r_MP2SYGeyafrDYPy109sUn5Nzx0OQ6QOxLexCiw",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMyIsInR5cGUiOiJyZWZyZXNoIiwiZXhwIjoxNzcyOTY1MDEwfQ.tczDp3tdDMh_E_d6LCiOv_Wyb2BT7Xs5cnB7T-92Ios"
# }