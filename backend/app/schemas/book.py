from pydantic import BaseModel, Field


class BookSummary(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)


class BookDetail(BookSummary):
    language: str
    word_count: int
    source_url: str


class BookList(BaseModel):
    total: int
    offset: int
    limit: int
    results: list[BookSummary]
