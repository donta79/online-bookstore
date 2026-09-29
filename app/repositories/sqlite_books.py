import sqlite3
from pathlib import Path

from app.models.book_models import Book


class SQLiteBookRepository:
    def __init__(self, database_path: str | Path) -> None:
        self._database_path = str(database_path)
        self._memory_connection: sqlite3.Connection | None = None
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            self._memory_connection = sqlite3.connect(
                self._database_path, check_same_thread=False
            )
            self._memory_connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def list_books(self) -> list[Book]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, author, isbn, description, availability
                FROM books
                ORDER BY id
                """
            ).fetchall()
        return [self._to_book(row) for row in rows]

    def find_by_id(self, book_id: int) -> Book | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, author, isbn, description, availability
                FROM books
                WHERE id = ?
                """,
                (book_id,),
            ).fetchone()
        return self._to_book(row) if row is not None else None

    def search_books(self, query: str) -> list[Book]:
        normalized_query = query.strip()
        if not normalized_query:
            return self.list_books()

        pattern = f"%{normalized_query}%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, author, isbn, description, availability
                FROM books
                WHERE title LIKE ? COLLATE NOCASE
                   OR author LIKE ? COLLATE NOCASE
                   OR description LIKE ? COLLATE NOCASE
                ORDER BY id
                """,
                (pattern, pattern, pattern),
            ).fetchall()
        return [self._to_book(row) for row in rows]

    def find_by_isbn_case_insensitive(self, isbn: str) -> Book | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, author, isbn, description, availability
                FROM books
                WHERE isbn = ? COLLATE NOCASE
                """,
                (isbn,),
            ).fetchone()
        return self._to_book(row) if row is not None else None

    def delete_book(self, book_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        return cursor.rowcount == 1

    def update_book(
        self,
        book_id: int,
        *,
        title: str,
        author: str,
        isbn: str,
        description: str,
        availability: bool,
    ) -> Book | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE books
                SET title = ?, author = ?, isbn = ?, description = ?, availability = ?
                WHERE id = ?
                """,
                (title, author, isbn, description, availability, book_id),
            )
        return (
            Book(
                id=book_id,
                title=title,
                author=author,
                isbn=isbn,
                description=description,
                availability=availability,
            )
            if cursor.rowcount == 1
            else None
        )

    def create_book(
        self,
        *,
        title: str,
        author: str,
        isbn: str,
        description: str,
        availability: bool,
    ) -> Book:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO books (title, author, isbn, description, availability)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, author, isbn, description, availability),
            )
        return Book(
            id=cursor.lastrowid,
            title=title,
            author=author,
            isbn=isbn,
            description=description,
            availability=availability,
        )

    def _connect(self) -> sqlite3.Connection:
        if self._memory_connection is not None:
            return self._memory_connection

        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    isbn TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    description TEXT NOT NULL,
                    availability INTEGER NOT NULL CHECK (availability IN (0, 1))
                )
                """
            )

    @staticmethod
    def _to_book(row: sqlite3.Row) -> Book:
        return Book(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            isbn=row["isbn"],
            description=row["description"],
            availability=bool(row["availability"]),
        )
