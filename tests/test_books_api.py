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
