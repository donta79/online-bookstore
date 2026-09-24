from fastapi.testclient import TestClient

from app.api.ai import get_summary_service
from app.ai.model_factory import ModelUnavailableError
from app.main import app


class StubSummaryService:
    def __init__(self) -> None:
        self.last_description: str | None = None
        self.should_raise_unavailable = False

    def summarize(self, description: str) -> str:
        self.last_description = description
        if self.should_raise_unavailable:
            raise ModelUnavailableError("unavailable")
        return "First concise sentence. Second concise sentence."


def build_client(service: StubSummaryService) -> TestClient:
    app.dependency_overrides[get_summary_service] = lambda: service
    return TestClient(app)


def test_post_summaries_returns_summary() -> None:
    service = StubSummaryService()
    with build_client(service) as client:
        response = client.post(
            "/api/ai/summaries",
            json={"description": "A practical guide to software design."},
        )

        assert response.status_code == 200
        assert response.json() == {"summary": "First concise sentence. Second concise sentence."}


def test_post_summaries_sends_selected_description() -> None:
    service = StubSummaryService()
    description = "A detective investigates a mysterious theft at sea."

    with build_client(service) as client:
        response = client.post("/api/ai/summaries", json={"description": description})

        assert response.status_code == 200
        assert service.last_description == description


def test_post_summaries_returns_503_when_model_unavailable() -> None:
    service = StubSummaryService()
    service.should_raise_unavailable = True

    with build_client(service) as client:
        response = client.post(
            "/api/ai/summaries",
            json={"description": "A concise description."},
        )

        assert response.status_code == 503
        assert response.json() == {"detail": "Configured AI model is unavailable"}


def test_post_summaries_blank_description_returns_422() -> None:
    service = StubSummaryService()
    with build_client(service) as client:
        response = client.post("/api/ai/summaries", json={"description": "   "})

        assert response.status_code == 422
