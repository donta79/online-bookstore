from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.model_factory import ModelUnavailableError
from app.models.book_models import SummaryRequest, SummaryResponse
from app.services.ai_summary_service import SummaryService

router = APIRouter(prefix="/api/ai", tags=["ai"])

_summary_service = SummaryService()


def get_summary_service() -> SummaryService:
    return _summary_service


@router.post("/summaries", response_model=SummaryResponse)
def summarize_book_description(
    payload: SummaryRequest,
    service: SummaryService = Depends(get_summary_service),
) -> SummaryResponse:
    try:
        summary = service.summarize(payload.description)
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configured AI model is unavailable",
        ) from exc

    return SummaryResponse(summary=summary)
