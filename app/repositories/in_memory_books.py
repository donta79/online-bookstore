from app.models.book_models import Book


class InMemoryBookRepository:
    def __init__(self) -> None:
        self._books: list[Book] = []
        self._next_id = 1

    def list_books(self) -> list[Book]:
        return list(self._books)

    def search_books(self, query: str) -> list[Book]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return self.list_books()

        return [
            book
            for book in self._books
            if normalized_query in book.title.lower()
            or normalized_query in book.author.lower()
            or normalized_query in book.description.lower()
        ]

    def find_by_isbn_case_insensitive(self, isbn: str) -> Book | None:
        normalized = isbn.lower()
        return next((book for book in self._books if book.isbn.lower() == normalized), None)

    def create_book(
        self,
        *,
        title: str,
        author: str,
        isbn: str,
        description: str,
        availability: bool,
    ) -> Book:
        book = Book(
            id=self._next_id,
            title=title,
            author=author,
            isbn=isbn,
            description=description,
            availability=availability,
        )
        self._books.append(book)
        self._next_id += 1
        return book
