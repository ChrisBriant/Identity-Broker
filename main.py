from fastapi import FastAPI
from auth.routes import router as auth_router
import os
import dotenv

# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

app = FastAPI()

app.include_router(auth_router, prefix="/auth")