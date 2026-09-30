from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.ai.model_factory import ModelUnavailableError
from app.models.pdf_rag_models import (
    PdfRagDocumentResponse,
    PdfRagQuestionRequest,
    PdfRagQuestionResponse,
)
from app.services.pdf_rag_service import (
    PdfDocumentNotFoundError,
    PdfDocumentValidationError,
    PdfRagService,
)

router = APIRouter(prefix="/api/ai/pdf-rag", tags=["pdf-rag"])

_pdf_rag_service = PdfRagService()


def get_pdf_rag_service() -> PdfRagService:
    return _pdf_rag_service


@router.post("/documents", response_model=PdfRagDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_document(
    file: Annotated[UploadFile, File(...)],
    service: PdfRagService = Depends(get_pdf_rag_service),
) -> PdfRagDocumentResponse:
    try:
        return service.index_document(file.filename, file.content_type, await file.read())
    except PdfDocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc


@router.post("/questions", response_model=PdfRagQuestionResponse)
def ask_pdf_question(
    payload: PdfRagQuestionRequest,
    service: PdfRagService = Depends(get_pdf_rag_service),
) -> PdfRagQuestionResponse:
    try:
        return service.answer_question(payload.question)
    except PdfDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF document has been uploaded",
        ) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configured AI model is unavailable",
        ) from exc
