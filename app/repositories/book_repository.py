from typing import Protocol

from app.models.book_models import Book


class BookRepository(Protocol):
    def list_books(self) -> list[Book]: ...

    def find_by_id(self, book_id: int) -> Book | None: ...

    def search_books(self, query: str) -> list[Book]: ...

    def find_by_isbn_case_insensitive(self, isbn: str) -> Book | None: ...

    def delete_book(self, book_id: int) -> bool: ...

    def update_book(
        self,
        book_id: int,
        *,
        title: str,
        author: str,
        isbn: str,
        description: str,
        availability: bool,
    ) -> Book | None: ...

    def create_book(
        self,
        *,
        title: str,
        author: str,
        isbn: str,
        description: str,
        availability: bool,
    ) -> Book: ...
