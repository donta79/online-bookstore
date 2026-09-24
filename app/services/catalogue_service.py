from app.models.book_models import Book, BookCreate
from app.repositories.in_memory_books import InMemoryBookRepository


class DuplicateIsbnError(Exception):
    pass


class CatalogueService:
    def __init__(self, repository: InMemoryBookRepository) -> None:
        self._repository = repository

    def list_books(self, query: str | None = None) -> list[Book]:
        if query is None:
            return self._repository.list_books()

        return self._repository.search_books(query)

    def add_book(self, payload: BookCreate) -> Book:
        if self._repository.find_by_isbn_case_insensitive(payload.isbn):
            raise DuplicateIsbnError(payload.isbn)

        return self._repository.create_book(
            title=payload.title,
            author=payload.author,
            isbn=payload.isbn,
            description=payload.description,
            availability=payload.availability,
        )
