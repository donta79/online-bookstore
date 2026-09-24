from fastapi.testclient import TestClient

from app.api.books import get_catalogue_service
from app.main import app
from app.repositories.in_memory_books import InMemoryBookRepository
from app.services.catalogue_service import CatalogueService


def build_client() -> TestClient:
    repository = InMemoryBookRepository()
    service = CatalogueService(repository)
    app.dependency_overrides[get_catalogue_service] = lambda: service
    return TestClient(app)


def seed_books(client: TestClient) -> None:
    books = [
        {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "ISBN-001",
            "description": "Software craftsmanship guide.",
            "availability": True,
        },
        {
            "title": "Domain-Driven Design",
            "author": "Eric Evans",
            "isbn": "ISBN-002",
            "description": "A guide to complex software design.",
            "availability": False,
        },
        {
            "title": "Pragmatic Programmer",
            "author": "Andy Hunt",
            "isbn": "ISBN-003",
            "description": "Classic guidance for programmers.",
            "availability": True,
        },
    ]
    for book in books:
        response = client.post("/api/books", json=book)
        assert response.status_code == 201


def test_create_book_success_returns_201_and_assigned_id() -> None:
    with build_client() as client:
        response = client.post(
            "/api/books",
            json={
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "ISBN-123",
                "description": "A software craftsmanship classic.",
                "availability": True,
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["id"] == 1
        assert body["title"] == "Clean Code"

        books_response = client.get("/api/books")
        assert books_response.status_code == 200
        assert len(books_response.json()) == 1


def test_create_book_missing_required_field_returns_422() -> None:
    with build_client() as client:
        response = client.post(
            "/api/books",
            json={
                "title": "",
                "author": "Author",
                "isbn": "ISBN-234",
                "description": "Desc",
                "availability": True,
            },
        )

        assert response.status_code == 422


def test_create_book_duplicate_isbn_case_insensitive_returns_409() -> None:
    with build_client() as client:
        first = client.post(
            "/api/books",
            json={
                "title": "Book One",
                "author": "Author One",
                "isbn": "AbC-123",
                "description": "Desc one",
                "availability": True,
            },
        )
        assert first.status_code == 201

        second = client.post(
            "/api/books",
            json={
                "title": "Book Two",
                "author": "Author Two",
                "isbn": "aBc-123",
                "description": "Desc two",
                "availability": False,
            },
        )
        assert second.status_code == 409


def test_search_books_by_title_query() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books", params={"q": "clean"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["title"] == "Clean Code"


def test_search_books_by_author_query() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books", params={"q": "evans"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["author"] == "Eric Evans"


def test_search_books_by_description_query() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books", params={"q": "programmers"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["title"] == "Pragmatic Programmer"


def test_search_books_is_case_insensitive() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books", params={"q": "RoBeRt C. mArTiN"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["title"] == "Clean Code"


def test_search_books_blank_query_returns_all_books() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books", params={"q": "   "})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 3


def test_search_books_no_match_returns_empty_list() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books", params={"q": "no-such-book"})
        assert response.status_code == 200
        assert response.json() == []


def test_get_book_existing_id_returns_book_details() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books/2")

        assert response.status_code == 200
        assert response.json() == {
            "id": 2,
            "title": "Domain-Driven Design",
            "author": "Eric Evans",
            "isbn": "ISBN-002",
            "description": "A guide to complex software design.",
            "availability": False,
        }


def test_get_book_missing_id_returns_404() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.get("/api/books/999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Book not found"}
