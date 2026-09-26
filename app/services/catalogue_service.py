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

    def get_book(self, book_id: int) -> Book | None:
        return self._repository.find_by_id(book_id)

    def delete_book(self, book_id: int) -> bool:
        return self._repository.delete_book(book_id)

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

    def update_book(self, book_id: int, payload: BookCreate) -> Book | None:
        book = self._repository.find_by_id(book_id)
        if book is None:
            return None

        duplicate = self._repository.find_by_isbn_case_insensitive(payload.isbn)
        if duplicate is not None and duplicate.id != book_id:
            raise DuplicateIsbnError(payload.isbn)

        return self._repository.update_book(
            book_id,
            title=payload.title,
            author=payload.author,
            isbn=payload.isbn,
            description=payload.description,
            availability=payload.availability,
        )
