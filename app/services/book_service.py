from app.models.book_models import Book
from app.services.catalogue_service import CatalogueService


class BookNotFoundError(Exception):
    pass


class BookService:
    """Read-only catalogue operations used by AI tool calls."""

    def __init__(self, catalogue_service: CatalogueService) -> None:
        self._catalogue_service = catalogue_service

    def search_books(self, query: str) -> list[Book]:
        return self._catalogue_service.list_books(query)

    def check_availability(self, book_id: int) -> bool:
        book = self._catalogue_service.get_book(book_id)
        if book is None:
            raise BookNotFoundError(f"Book not found: {book_id}")
        return book.availability
