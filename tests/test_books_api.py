from fastapi.testclient import TestClient

from app.api.books import get_catalogue_service
from app.main import app
from app.repositories.sqlite_books import SQLiteBookRepository
from app.services.catalogue_service import CatalogueService


def build_client() -> TestClient:
    repository = SQLiteBookRepository(":memory:")
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


def test_books_persist_changes_across_repository_recreation(tmp_path) -> None:
    database_path = tmp_path / "bookstore.db"
    first_repository = SQLiteBookRepository(database_path)
    created = first_repository.create_book(
        title="Persistent Book",
        author="Ada Lovelace",
        isbn="ISBN-PERSIST",
        description="Stored in SQLite.",
        availability=True,
    )

    second_repository = SQLiteBookRepository(database_path)

    assert second_repository.find_by_id(created.id) == created
    updated = second_repository.update_book(
        created.id,
        title="Updated Persistent Book",
        author="Ada Lovelace",
        isbn="ISBN-PERSIST",
        description="Updated in SQLite.",
        availability=False,
    )

    third_repository = SQLiteBookRepository(database_path)

    assert third_repository.find_by_id(created.id) == updated
    assert third_repository.delete_book(created.id) is True

    fourth_repository = SQLiteBookRepository(database_path)

    assert fourth_repository.find_by_id(created.id) is None


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
        assert second.json() == {"detail": "ISBN already exists"}


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


def test_delete_book_existing_id_returns_204_without_response_body() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.delete("/api/books/2")

        assert response.status_code == 204
        assert response.content == b""


def test_delete_book_missing_id_returns_404() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.delete("/api/books/999")

        assert response.status_code == 404
        assert response.json() == {"detail": "Book not found"}


def test_delete_book_removes_only_selected_book() -> None:
    with build_client() as client:
        seed_books(client)

        delete_response = client.delete("/api/books/2")
        assert delete_response.status_code == 204

        books_response = client.get("/api/books")
        assert books_response.status_code == 200
        assert books_response.json() == [
            {
                "id": 1,
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "ISBN-001",
                "description": "Software craftsmanship guide.",
                "availability": True,
            },
            {
                "id": 3,
                "title": "Pragmatic Programmer",
                "author": "Andy Hunt",
                "isbn": "ISBN-003",
                "description": "Classic guidance for programmers.",
                "availability": True,
            },
        ]


def test_update_book_existing_id_returns_200_and_updated_book() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.put(
            "/api/books/2",
            json={
                "title": "Domain-Driven Design Distilled",
                "author": "Vaughn Vernon",
                "isbn": "ISBN-202",
                "description": "A shorter DDD guide.",
                "availability": True,
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "id": 2,
            "title": "Domain-Driven Design Distilled",
            "author": "Vaughn Vernon",
            "isbn": "ISBN-202",
            "description": "A shorter DDD guide.",
            "availability": True,
        }


def test_update_book_missing_id_returns_404() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.put(
            "/api/books/999",
            json={
                "title": "Unknown",
                "author": "Unknown",
                "isbn": "ISBN-999",
                "description": "Unknown",
                "availability": True,
            },
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Book not found"}


def test_update_book_missing_required_field_returns_422() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.put(
            "/api/books/2",
            json={
                "title": "  ",
                "author": "Valid Author",
                "isbn": "ISBN-777",
                "description": "Valid description",
                "availability": True,
            },
        )

        assert response.status_code == 422


def test_update_book_duplicate_isbn_case_insensitive_returns_409() -> None:
    with build_client() as client:
        seed_books(client)

        response = client.put(
            "/api/books/2",
            json={
                "title": "Domain-Driven Design",
                "author": "Eric Evans",
                "isbn": "isbn-001",
                "description": "A guide to complex software design.",
                "availability": False,
            },
        )

        assert response.status_code == 409
        assert response.json() == {"detail": "ISBN already exists"}


def test_update_book_preserves_other_books() -> None:
    with build_client() as client:
        seed_books(client)

        update_response = client.put(
            "/api/books/2",
            json={
                "title": "Domain-Driven Design Distilled",
                "author": "Vaughn Vernon",
                "isbn": "ISBN-202",
                "description": "A shorter DDD guide.",
                "availability": True,
            },
        )
        assert update_response.status_code == 200

        books_response = client.get("/api/books")
        assert books_response.status_code == 200
        assert books_response.json() == [
            {
                "id": 1,
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "ISBN-001",
                "description": "Software craftsmanship guide.",
                "availability": True,
            },
            {
                "id": 2,
                "title": "Domain-Driven Design Distilled",
                "author": "Vaughn Vernon",
                "isbn": "ISBN-202",
                "description": "A shorter DDD guide.",
                "availability": True,
            },
            {
                "id": 3,
                "title": "Pragmatic Programmer",
                "author": "Andy Hunt",
                "isbn": "ISBN-003",
                "description": "Classic guidance for programmers.",
                "availability": True,
            },
        ]
