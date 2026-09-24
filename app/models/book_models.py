from pydantic import BaseModel, Field, constr

RequiredText = constr(strip_whitespace=True, min_length=1)


class BookCreate(BaseModel):
    title: RequiredText
    author: RequiredText
    isbn: RequiredText
    description: RequiredText
    availability: bool


class Book(BaseModel):
    id: int = Field(ge=1)
    title: str
    author: str
    isbn: str
    description: str
    availability: bool


class SummaryRequest(BaseModel):
    description: RequiredText


class SummaryResponse(BaseModel):
    summary: str
