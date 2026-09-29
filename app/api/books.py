import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.models.book_models import Book, BookCreate
from app.repositories.sqlite_books import SQLiteBookRepository
from app.services.catalogue_service import CatalogueService, DuplicateIsbnError

router = APIRouter(prefix="/api/books", tags=["books"])

_repository = SQLiteBookRepository(
    os.environ.get("BOOKSTORE_DATABASE_PATH", Path("data") / "bookstore.db")
)
_catalogue_service = CatalogueService(_repository)


def get_catalogue_service() -> CatalogueService:
    return _catalogue_service


@router.get("", response_model=list[Book])
def list_books(
    q: str | None = None,
    service: CatalogueService = Depends(get_catalogue_service),
) -> list[Book]:
    return service.list_books(q)


@router.get("/{book_id}", response_model=Book)
def get_book(
    book_id: int,
    service: CatalogueService = Depends(get_catalogue_service),
) -> Book:
    book = service.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_book(
    book_id: int,
    service: CatalogueService = Depends(get_catalogue_service),
) -> Response:
    if not service.delete_book(book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{book_id}", response_model=Book)
def update_book(
    book_id: int,
    payload: BookCreate,
    service: CatalogueService = Depends(get_catalogue_service),
) -> Book:
    try:
        updated = service.update_book(book_id, payload)
    except DuplicateIsbnError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ISBN already exists",
        ) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    return updated


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
            detail="ISBN already exists",
        ) from exc
