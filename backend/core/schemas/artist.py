from pydantic import BaseModel, Field


class Artist(BaseModel):
    name: str = Field(..., example="name")
    genre: str = Field(..., example="genre")
    user_id: str = Field(..., examples="1")
