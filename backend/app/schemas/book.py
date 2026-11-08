
from pydantic import BaseModel, Field


class BookSummary(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
