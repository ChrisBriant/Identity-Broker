from sqlalchemy import select, func, insert, update, text
from sqlalchemy.dialects.postgresql import insert as pg_insert # Using for potential future optimization (ON CONFLICT)
from sqlalchemy.orm import selectinload
from .db import SessionLocal
from .models import Users
from utils.app_utils import create_random_username
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import math


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

            print("NEW USER", user)

            # --- Return the final user record details ---
            return {
                "id": user.id,
                "external_id": user.external_id,
                "idp": user.idp,
                "alias": user.alias,
                "new_user" : new_user_created,
                "email" : user.email
            }
    except Exception as e:
        # In a real application, you should log the error instead of just printing
        print(f"Error in get_or_add_user: {e}")
        return None