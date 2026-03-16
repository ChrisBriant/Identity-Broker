from fastapi import APIRouter, HTTPException, Request, Depends, Response, Query
from fastapi.responses import RedirectResponse
from providers.provider_registry import get_provider
from data.db_actions import (
    get_or_add_user, 
    add_feedback, 
    get_user, 
    get_feedback,
    create_auth_code,
    validate_auth_code,
)
import uuid
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
from data.shemas import (
    TokenSchema, 
    ProviderSchema, 
    UserProfileSchema, 
    FeedbackSchema,
    AuthCodeSchema,
)
from typing import List
from pathlib import Path
import json
import os
import bleach
import base64

router = APIRouter()

# Go to project root (adjust parents[n] if needed)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_REDIRECTS = [
    "uk.chrisbriant.idbroker://callback",
]


@router.get("/providers", response_model = List[ProviderSchema])
async def get_providers():
    """
        Helper which lists the providers with a media link and login link.
        It reads from the providers.json file and creates the response object
    """

    providers_path = PROJECT_ROOT / "providers" / "providers.json"

    with open(providers_path, "r", encoding="utf-8") as f:
        providers = json.load(f)

    provider_list = [ ProviderSchema(
        id=p['id'], 
        name=p['name'],
        logo= f"{os.environ.get("BACKEND_REDIRECT_URI")}{p['logo']}",
        login= f"{os.environ.get("BACKEND_REDIRECT_URI")}/auth/{p['id']}/login"
    ) for p in providers]
    return provider_list

# @router.get("/auth/{provider}/login")
# async def login(provider: str):
#     try:
#         idp = get_provider(provider)
#     except ValueError:
#         raise HTTPException(
#             status_code=404,
#             detail="Provider not found"
#         )
#     except Exception as e:
#         #Catch all
#         raise HTTPException(
#             status_code=400,
#             detail=f"An error occurred retrieving the provider {e}"
#         ) 
#     return {"auth_url": await idp.get_auth_url()}

@router.get("/{provider}/login")
async def login(provider: str,redirect_uri: str | None = Query(None),set_cookie : bool = Query(True)):
    """
        Performs the login to the IDP using their authorisation endpoint. It then redirects to the token exchange endpoint.
        Example: https://localhost:8000/auth/linkedin/login
    """

    idp = get_provider(provider)

    # Generate secure state
    #state = str(uuid.uuid4())

    if(redirect_uri):
        print("REDIRECT URI EXISTS", redirect_uri)
        #Check on allowed redirects list
        if redirect_uri not in ALLOWED_REDIRECTS :
            print("REDIRECT NOT AUTHORIZED")
            return RedirectResponse(f"{redirect_uri}?error=unauthorised")
            #raise HTTPException(status_code=401,detail="Redirect URI is not authorized.")
        else:
            print("REDIRECT IS AUTHORIZED")
    else:
        print("REDIRECT URI DOES NOT EXIST", redirect_uri)

    #The redirect uri is encoded in the state data, this is for redirects from different clients, e.g. android, web
    state_data = {
        "csrf": str(uuid.uuid4()),
        "redirect_uri": redirect_uri,
        "set_cookie" : set_cookie
    }
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    auth_url = await idp.get_auth_url(state)
    print("THIS IS THE AUTH URL", auth_url)

    #if redirect_uri and "localhost" in redirect_uri:
    # print("REPLACING REDIRECT URL")
    # auth_url = auth_url.replace("localhost", "10.0.2.2")


    # Redirect browser immediately
    response = RedirectResponse(auth_url)

    # Store state in a cookie
    response.set_cookie(
        key=f"oauth_state_{provider}",
        value=state,
        httponly=True,
        secure=True,
        samesite="none"
    )

    return response


# @router.get("/{provider}/callback", response_model=TokenSchema)
# async def auth_callback(provider: str, code: str):

#     idp = get_provider(provider)

#     access_token = await idp.exchange_code(code)

#     #access_token = "MTQ4MDA3NDQ2NTExNDMyOTI5MQ.uv6PGkQHeeSpcUUhAv23WRQwqF4WON"

#     user_profile = await idp.get_user_info(access_token)


#     # print("DISCORD PROFILE ", user_profile, access_token)

#     # user_profile = {
#     #     'id': '112023773581453384433', 
#     #     'email': 'cbri4nt@gmail.com', 
#     #     'verified_email': True, 
#     #     'name': 'Chris Briant', 
#     #     'given_name': 'Chris', 
#     #     'family_name': 'Briant', 
#     #     'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIf1fisJjPwLJ6e9uMk_Q46nWohbOwoeP7Gw4b3EwQw0E15fA=s96-c'
#     # }

#     # print("USER PROFILE RETRIEVED", user_profile)

#     # database logic here
#     user_record = await get_or_add_user(user_profile["id"],provider,None,user_profile['email'])
#     if not user_record:
#         raise HTTPException(
#             status_code=400,
#             detail="Failed to create the user"
#         )
#     print("USER FROM DATABASE", user_record)
#     #Issue a JWT
#     jwt_token_pair = obtain_jwt_pair(user_record["id"],user_record["idp"], user_record["alias"]) 
#     print("JWT OBTAINED", jwt_token_pair)

#     response = TokenSchema(
#         access_token = jwt_token_pair['access'],
#         refresh_token = jwt_token_pair['refresh'],
#     )

#     return response

# #TEST ROUTE FOR IP INFORMATION
# @router.get("/ip-info")
# async def ip_info(request: Request):

#     ip_address = request.client.host
#     user_agent = request.headers.get("user-agent")

#     return {
#         "ip": ip_address,
#         "user_agent": user_agent
#     }

@router.get("/{provider}/callback", response_model=str)
async def auth_callback_with_redirect(request: Request, provider: str, code: str, state: str | None = Query(None)):
    """
        Handles the callback from the IDP
        1. Takes the code from the payload and exchanges it for a token
        2. The token is verified and the user profile data returned
        3. User profile data is stored in the database
        4. JWT token is issued and set within the session cookie
    """


    idp = get_provider(provider)

    #Handle the state if it is in the payload
    stored_state = request.cookies.get(f"oauth_state_{provider}")
    if state:
        print("STATES", stored_state, state)
        if stored_state != state:
            raise HTTPException(status_code=401,detail="Invalid state")
    #Check for redirect URI in stored_state
    state_data = json.loads(base64.urlsafe_b64decode(stored_state).decode())
    redirect_uri = state_data.get("redirect_uri")
    set_cookie = state_data.get("set_cookie")
    print("REDIRECT URI IS ", redirect_uri, set_cookie)

    #State is passed in as some providers need to pass it to the token endpoint
    access_token = await idp.exchange_code(code, state)



    #access_token = "MTQ4MDA3NDQ2NTExNDMyOTI5MQ.uv6PGkQHeeSpcUUhAv23WRQwqF4WON"
    #Verify the token and return the user profile data
    user_profile = await idp.get_user_info(access_token)

    # print("USER PROFILE", user_profile)

    # return "Hello"

    # database logic here
    user_record = await get_or_add_user(str(user_profile["id"]),provider,None,user_profile['email'])
    if not user_record:
        raise HTTPException(
            status_code=400,
            detail="Failed to create the user"
        )
    print("USER FROM DATABASE", user_record)
    #Issue a JWT
    jwt_token_pair = obtain_jwt_pair(str(user_record["id"]),user_record["idp"], user_record["alias"]) 
    print("JWT OBTAINED", jwt_token_pair)

    #Set the redirect URI depending on whether it exists in the cookie set to default if not in cookie
    response_redirect_uri = redirect_uri if redirect_uri else os.environ.get("CLIENT_REDIRECT_URI")

    response = RedirectResponse(
        url=response_redirect_uri,
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


@router.post("/postfeedback", response_model=FeedbackSchema)
async def post_feedback(feedback : str, token_data = Depends(validate_jwt_cookie)):
    """
        Allow authenticated users to post feedback

    """
    if token_data:
        #Sanitize the feedback text sent by the user
        cleaned_feedback = bleach.clean(feedback, tags=[], attributes={}, strip=True)
        #Add sanitized feedback to the database
        feedback_data = await add_feedback(token_data['user_id'], cleaned_feedback)
        feedback_response = FeedbackSchema.model_validate(feedback_data)
        print("TOKEN DATA", token_data, feedback_data)
    else :
        raise HTTPException(status_code=401, detail="Invalid token")
    return feedback_response

@router.get("/getfeedback", response_model=List[FeedbackSchema])
async def get_feedback_responses(token_data = Depends(validate_jwt_cookie)):
    #Get the user
    user = await get_user(int(token_data['user_id']))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.admin:
        raise HTTPException(status_code=403, detail="You do not have permission to retrieve feedback")
    #Get the feedback
    feedback = await get_feedback()
    feedback_response = [ FeedbackSchema.model_validate(feedback_data) for feedback_data in feedback ]
    return feedback_response


@router.post("/logout")
def logout(response: Response):
    """
        Logs out the user by clearing the Cookies
    """
    # response.delete_cookie("access_token")
    # response.delete_cookie("refresh_token")

    response.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        samesite="none",
    )

    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=True,
        samesite="none",
    )
    return {"status": "logged_out"}


# @router.get("/issuejwt", response_model=TokenSchema)
# async def issue_jwt (id: str, idp:str, alias:str):
#     jwt_token_pair = obtain_jwt_pair(id,idp,alias)
#     response = TokenSchema(
#         access_token = jwt_token_pair['access'],
#         refresh_token = jwt_token_pair['refresh'],
#     )

#     return response


# @router.get("/issuejwtredirect")
# async def issue_jwt_redirect(id: str, idp: str, alias: str):

#     jwt_token_pair = obtain_jwt_pair(id, idp, alias)

#     response = RedirectResponse(
#         url=os.environ.get("CLIENT_REDIRECT_URI"),
#         status_code=302
#     )

#     print("RESPONSE OBJECT", os.environ.get("CLIENT_REDIRECT_URI"))

#     # Access token cookie
#     response.set_cookie(
#         key="access_token",
#         value=jwt_token_pair["access"],
#         httponly=True,
#         secure=True,          # HTTPS only
#         samesite="lax",
#         max_age=ACCESS_TOKEN_LIFETIME          
#     )

#     # Refresh token cookie
#     response.set_cookie(
#         key="refresh_token",
#         value=jwt_token_pair["refresh"],
#         httponly=True,
#         secure=True,
#         samesite="lax",
#         max_age=REFRESH_TOKEN_LIFETIME  
#     )

#     return response

# @router.get("/refresh", response_model=TokenSchema)
# async def refresh_jwt (request:Request):
#     refresh_token = request.cookies.get("refresh_token")

#     try:
#         print("HERE IS THE REFRESH", request.cookies.get("refresh_token"))
#         jwt_token_pair = refresh_jwt_pair(refresh_token)
#     except RefreshTokenExpiredError as ex_err:
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token has expired"
#         )
#     except InvalidRefreshTokenError as invalid_token_err:
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token is invalid"
#         )
#     except Exception as e:
#         print("AN ERROR OCCURRED REFRESHING THE TOKEN", e)
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token is invalid"
#         )

#     response = RedirectResponse(
#         url=os.environ.get("CLIENT_REDIRECT_URI"),
#         status_code=302
#     )

#     # Access token cookie
#     response.set_cookie(
#         key="access_token",
#         value=jwt_token_pair["access"],
#         httponly=True,
#         secure=True,          # HTTPS only
#         samesite="none",
#         max_age=ACCESS_TOKEN_LIFETIME
#     )

#     # Refresh token cookie
#     response.set_cookie(
#         key="refresh_token",
#         value=jwt_token_pair["refresh"],
#         httponly=True,
#         secure=True,
#         samesite="none",
#         max_age=REFRESH_TOKEN_LIFETIME
#     )

#     return response

@router.post("/refresh")
async def refresh_jwt(request: Request, response: Response):
    """
        Takes the refresh token and issues a new token pair and sets the session cookie
    """

    refresh_token = request.cookies.get("refresh_token")

    try:
        jwt_token_pair = refresh_jwt_pair(refresh_token)

    except RefreshTokenExpiredError:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    except InvalidRefreshTokenError:
        raise HTTPException(status_code=401, detail="Refresh token invalid")

    # Set new cookies
    response.set_cookie(
        key="access_token",
        value=jwt_token_pair["access"],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_LIFETIME
    )

    response.set_cookie(
        key="refresh_token",
        value=jwt_token_pair["refresh"],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_LIFETIME
    )

    return {"status": "refreshed"}



# @router.post("/refreshtoken", response_model=TokenSchema)
# async def refresh_jwt_token (refresh_token:str):
#     try:
#         jwt_token_pair = refresh_jwt_pair(refresh_token)
#     except RefreshTokenExpiredError as ex_err:
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token has expired"
#         )
#     except InvalidRefreshTokenError as invalid_token_err:
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token is invalid"
#         )
#     except Exception as e:
#         print("AN ERROR OCCURRED REFRESHING THE TOKEN")
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token is invalid"
#         )
        
#     response = TokenSchema(
#         access_token = jwt_token_pair['access'],
#         refresh_token = jwt_token_pair['refresh'],
#     )

#     return response

@router.post("/exchangeauthcodeforjwt", response_model=TokenSchema)
async def exchange_auth_code_for_jwt(auth_code : AuthCodeSchema):
    """
        This endpoint is called by the client to exchange an auth code for a JWT token and return the response as Json
        This is designed to support authorisation flows where there isn't an option of setting an authorisaton cookie
    """
    #Get the user from the database if the code is valid
    user = await validate_auth_code(auth_code.auth_code)
    if not user:
        raise HTTPException(status_code=401,detail="Authorisation code is invalid")
    
    jwt_token_pair = obtain_jwt_pair(user.id, user.idp, user.alias)

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