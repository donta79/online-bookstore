from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.catalog_agent import CatalogueAgentError
from app.ai.model_factory import ModelUnavailableError
from app.api.books import get_catalogue_service
from app.models.book_models import AgentCatalogRequest, AgentCatalogResponse
from app.services.book_service import BookService
from app.services.catalog_agent_service import CatalogAgentService
from app.services.catalogue_service import CatalogueService

router = APIRouter(prefix="/api/agent", tags=["agent"])


def get_catalog_agent_service(
    catalogue_service: CatalogueService = Depends(get_catalogue_service),
) -> CatalogAgentService:
    return CatalogAgentService(BookService(catalogue_service))


@router.post("/catalog", response_model=AgentCatalogResponse)
def ask_catalog_agent(
    payload: AgentCatalogRequest,
    service: CatalogAgentService = Depends(get_catalog_agent_service),
) -> AgentCatalogResponse:
    try:
        answer, results = service.ask(payload.question)
    except (ModelUnavailableError, CatalogueAgentError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalogue agent is unavailable",
        ) from exc

    return AgentCatalogResponse(answer=answer, results=results)
