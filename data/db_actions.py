from sqlalchemy import select, func, insert, update, text
from sqlalchemy.dialects.postgresql import insert as pg_insert # Using for potential future optimization (ON CONFLICT)
from sqlalchemy.orm import selectinload
from .db import SessionLocal
from .models import Users, Feedback, AuthCode
from utils.app_utils import create_random_username
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import math
import uuid
import asyncio

class DatabaseUpdateError(Exception):
    pass

async def get_or_add_user(external_id: str, idp: str, alias: str | None, email: str) -> dict | None:
    new_user_created = False
    
    try:
        async with SessionLocal() as session:
            #Find the user and return record or none
            stmt = select(Users).where(
                (Users.external_id == external_id) & (Users.idp == idp)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            #If not found then create a user in the database
            if user is None:
                #Set the new user flag
                new_user_created = True
                # Use the alias provided in the function argument, or generate a new one if None
                new_alias = alias if alias is not None else create_random_username()
                
                # Create the new user object
                new_user = Users(
                    external_id=external_id,
                    idp=idp,
                    alias=new_alias,
                    email=email,
                )
                
                # Add and commit to the database
                session.add(new_user)
                await session.commit()
                
                # Refresh to get the auto-generated primary key (id) and ensure data is loaded
                # We need to refresh/expire to use the newly generated primary key in the return value
                await session.refresh(new_user) 
                
                user = new_user

            if user.alias is None:
                new_alias = create_random_username()
                
                # Update the record in the database
                update_stmt = update(Users).where(Users.id == user.id).values(alias=new_alias)
                await session.execute(update_stmt)
                await session.commit()
                
                # Update the user object in memory for the return value
                user.alias = new_alias

            # --- Return the final user record details ---
            return {
                "id": user.id,
                "external_id": user.external_id,
                "idp": user.idp,
                "alias": user.alias,
                "new_user" : new_user_created,
                "email" : user.email,
                "terms_accepted" : user.terms_accepted
            }
    except Exception as e:
        # In a real application, you should log the error instead of just printing
        print(f"Error in get_or_add_user: {e}")
        return None
    
async def get_user(user_id: int) -> Users:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Users).where(Users.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user
    
    
async def add_feedback(user_id: int, message: str) -> Feedback:
    """
    Create a new feedback entry for a given user.

    Args:
        db (Session): SQLAlchemy database session.
        user_id (int): ID of the user submitting feedback.
        message (str): The feedback message.

    Returns:
        Feedback: The newly created Feedback object.
    """
    try:
        async with SessionLocal() as session:

            new_feedback = Feedback(
                user_id=int(user_id),
                message=message
            )

            session.add(new_feedback)
            await session.commit()

            result = await session.execute(
                select(Feedback)
                .options(selectinload(Feedback.user))
                .where(Feedback.id == new_feedback.id)
            )
    except Exception as e:
        # In a real application, you should log the error instead of just printing
        print(f"Error in add_feedback: {e}")
        return None
    return new_feedback

async def get_feedback() -> List[Feedback]:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Feedback).options(selectinload(Feedback.user))
        )
        return result.scalars().all()
    
#SET THE AUTHCODE LIFETIME
AUTH_CODE_LIFETIME = 300


#The following is for authentication codes which will be used for a mechanism for mobile devices as a solution to the problem where cookies cannot be extracted from the browser session
async def create_auth_code(user_id: int) -> AuthCode:
    """
        Create an authcode in the database.
        This is for use with authentication flows that cannot extract the token from the cookie
        It will set an authcode that will be checked by another endpoint which validates it and returns a token pair if successful
    """

    try:
        async with SessionLocal() as session:
            new_code = AuthCode(
                code=str(uuid.uuid4()),
                user_id=user_id,
                used=False
            )
            session.add(new_code)
            await session.commit()
            await session.refresh(new_code)
    except Exception as e:
        # In a real application, you should log the error instead of just printing
        print(f"Error in create_auth_code: {e}")
        return None
    return new_code



async def validate_auth_code(code: str) -> Users:
    """
    Check if an auth code exists and is within expiry.
    If valid, mark as used and return a user object.
    Otherwise return None.
    """
    try:
        async with SessionLocal() as session:
            # Lookup the auth code
            result = await session.execute(select(AuthCode).where(AuthCode.code == code))
            auth_code = result.scalars().first()

            if not auth_code:
                return None  # code does not exist

            # Check if already used
            if auth_code.used:
                return None

            # Check expiry
            now = datetime.now(timezone.utc)
            created_at_aware = auth_code.created_at.replace(tzinfo=timezone.utc)
            if created_at_aware + timedelta(seconds=AUTH_CODE_LIFETIME) < now:
                return None

            # Mark as used
            auth_code.used = True
            session.add(auth_code)
            await session.commit()
            result = await session.execute(
                select(Users).where(Users.id == auth_code.user_id)
            )
            user = result.scalar_one_or_none()
            return user
    except Exception as e:
        # In a real application, you should log the error instead of just printing
        print(f"Error in validate_auth_code: {e}")
        return None

async def update_terms_accepted(user_id: int) :
    """
        Update the users table to accept the terms and conditions
    """
    try:
        async with SessionLocal() as session:
                update_stmt = update(Users).where(Users.id == int(user_id)).values(terms_accepted=True)
                await session.execute(update_stmt)
                await session.commit()
    except Exception as e:
        # In a real application, you should log the error instead of just printing
        print(f"Error in update_terms_accepted: {e}")
        #Raise exception so that error propagates
        raise DatabaseUpdateError()                 



async def main():
    #For testing purposes
    auth_code = await create_auth_code(1)

if __name__ == "__main__":
    asyncio.run(main())