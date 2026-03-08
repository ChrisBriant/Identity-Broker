from fastapi import APIRouter, HTTPException, Request
from providers.provider_registry import get_provider
from data.db_actions import get_or_add_user
from .token import obtain_jwt_token, obtain_jwt_pair
from data.shemas import TokenSchema, ProviderSchema
from typing import List
from pathlib import Path
import json

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