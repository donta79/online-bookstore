from pydantic import BaseModel, Field, constr

RequiredQuestion = constr(strip_whitespace=True, min_length=1)


class PdfRagDocumentResponse(BaseModel):
    document_name: str
    page_count: int = Field(ge=1)
    chunk_count: int = Field(ge=1)


class PdfRagQuestionRequest(BaseModel):
    question: RequiredQuestion


class PdfRagSource(BaseModel):
    excerpt: str
    page_number: int = Field(ge=1)


class PdfRagQuestionResponse(BaseModel):
    answer: str
    sources: list[PdfRagSource] = Field(default_factory=list)
    insufficient_context: bool
