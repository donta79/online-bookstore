from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.ai.model_factory import ModelUnavailableError
from app.api.pdf_rag import get_pdf_rag_service
from app.main import app
from app.services.pdf_rag_service import PdfRagService


class FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class FakePdfReader:
    def __init__(self, _: object) -> None:
        self.pages = [
            FakePage("The bookstore opens at nine in the morning on weekdays."),
            FakePage("Returns are accepted within thirty days with a receipt."),
        ]


class FakeResponse:
    content = "The bookstore opens at nine in the morning on weekdays."


class FakeModel:
    def invoke(self, _: object) -> FakeResponse:
        return FakeResponse()


@contextmanager
def client_for(service: PdfRagService):
    app.dependency_overrides[get_pdf_rag_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def upload_pdf(client: TestClient) -> object:
    return client.post(
        "/api/ai/pdf-rag/documents",
        files={"file": ("guide.pdf", b"%PDF-1.7 fake document", "application/pdf")},
    )


def test_upload_indexes_pdf_and_reports_active_document(monkeypatch) -> None:
    monkeypatch.setattr("app.services.pdf_rag_service.PdfReader", FakePdfReader)
    service = PdfRagService()

    with client_for(service) as client:
        response = upload_pdf(client)

    assert response.status_code == 201
    assert response.json() == {
        "document_name": "guide.pdf",
        "page_count": 2,
        "chunk_count": 2,
    }


def test_upload_rejects_missing_invalid_and_non_pdf_files() -> None:
    service = PdfRagService()

    with client_for(service) as client:
        missing = client.post("/api/ai/pdf-rag/documents")
        non_pdf = client.post(
            "/api/ai/pdf-rag/documents",
            files={"file": ("guide.txt", b"plain text", "text/plain")},
        )
        invalid = client.post(
            "/api/ai/pdf-rag/documents",
            files={"file": ("guide.pdf", b"not a PDF", "application/pdf")},
        )

    assert missing.status_code == 422
    assert non_pdf.status_code == 422
    assert invalid.status_code == 422


def test_question_returns_grounded_answer_with_page_numbered_source(monkeypatch) -> None:
    monkeypatch.setattr("app.services.pdf_rag_service.PdfReader", FakePdfReader)
    monkeypatch.setattr(
        "app.services.pdf_rag_service.ChatModelFactory.create",
        lambda _: FakeModel(),
    )
    service = PdfRagService()

    with client_for(service) as client:
        upload_pdf(client)
        response = client.post(
            "/api/ai/pdf-rag/questions",
            json={"question": "When does the bookstore open?"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The bookstore opens at nine in the morning on weekdays.",
        "sources": [
            {
                "excerpt": "The bookstore opens at nine in the morning on weekdays.",
                "page_number": 1,
            }
        ],
        "insufficient_context": False,
    }


def test_question_returns_explicit_insufficient_context_without_model(monkeypatch) -> None:
    monkeypatch.setattr("app.services.pdf_rag_service.PdfReader", FakePdfReader)
    service = PdfRagService()

    with client_for(service) as client:
        upload_pdf(client)
        response = client.post(
            "/api/ai/pdf-rag/questions",
            json={"question": "What is the capital of France?"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "I do not have enough information in the uploaded document to answer that.",
        "sources": [],
        "insufficient_context": True,
    }


def test_question_without_document_returns_404() -> None:
    with client_for(PdfRagService()) as client:
        response = client.post(
            "/api/ai/pdf-rag/questions",
            json={"question": "When does the store open?"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "No PDF document has been uploaded"}


def test_question_returns_503_when_model_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("app.services.pdf_rag_service.PdfReader", FakePdfReader)

    def unavailable(_: object) -> FakeModel:
        raise ModelUnavailableError("unavailable")

    monkeypatch.setattr(
        "app.services.pdf_rag_service.ChatModelFactory.create",
        unavailable,
    )
    service = PdfRagService()

    with client_for(service) as client:
        upload_pdf(client)
        response = client.post(
            "/api/ai/pdf-rag/questions",
            json={"question": "When does the bookstore open?"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Configured AI model is unavailable"}
