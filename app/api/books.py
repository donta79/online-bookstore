from fastapi import APIRouter, Depends, HTTPException, status

from app.models.book_models import Book, BookCreate
from app.repositories.in_memory_books import InMemoryBookRepository
from app.services.catalogue_service import CatalogueService, DuplicateIsbnError

router = APIRouter(prefix="/api/books", tags=["books"])

_repository = InMemoryBookRepository()
_catalogue_service = CatalogueService(_repository)


def get_catalogue_service() -> CatalogueService:
    return _catalogue_service


@router.get("", response_model=list[Book])
def list_books(service: CatalogueService = Depends(get_catalogue_service)) -> list[Book]:
    return service.list_books()


@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    service: CatalogueService = Depends(get_catalogue_service),
) -> Book:
    try:
        return service.add_book(payload)
    except DuplicateIsbnError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ISBN already exists: {exc}",
        ) from exc
