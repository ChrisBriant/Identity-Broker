from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from typing import List


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str

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

