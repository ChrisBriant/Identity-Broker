from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional
from datetime import datetime
from typing import List


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str

class ProviderSchema(BaseModel):
    id : str
    name : str
    logo : str
    login : str

class UserProfileSchema(BaseModel):
    id : int
    idp : str
    alias : str

class UserSchema(BaseModel):
    id: int
    alias: str

    model_config = ConfigDict(from_attributes=True)

class FeedbackSchema(BaseModel):
    id : int 
    # user_id : int
    message : str
    resolved : bool
    created_at : datetime
    updated_at : datetime
    user: UserSchema

    model_config = ConfigDict(from_attributes=True)

class FeedbackInputSchema(BaseModel):
    message : str

class AuthCodeSchema(BaseModel):
    auth_code : str

class RefreshTokenSchema(BaseModel):
    token : str | None

    # @computed_field
    # @property
    # def alias(self) -> str:
    #     return self.user.alias

# class WordWithoutSelectionSchema(BaseModel):
#     id: int
#     word: str

#     model_config = ConfigDict(from_attributes=True)

# class ClueWithSelectedWordsSchema(BaseModel):
#     clue : str
#     number_of_selected_words : int
#     words : List[WordWithoutSelectionSchema]

# class AIClueWithSelectedWordsSchema(BaseModel):
#     clue_id : int
#     clue : str
#     number_of_selected_words : int
#     created_at : datetime
#     words : List[WordSchema]

# class AIClueWithUnselectedWordsSchema(BaseModel):
#     clue_id : int
#     clue : str
#     number_of_selected_words : int
#     created_at : datetime
#     words : List[WordWithoutSelectionSchema]


# class AIGuessResponseSchema(BaseModel):
#     clue : str
#     number_of_selected_words : int
#     words : List[WordSchema]

