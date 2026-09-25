from fastapi.testclient import TestClient

from app.ai.catalog_agent import CatalogueAgentError
from app.ai.model_factory import ModelUnavailableError
from app.api.agent import get_catalog_agent_service
from app.main import app


class StubCatalogAgentService:
    def __init__(self) -> None:
        self.last_question: str | None = None
        self.mode = "success"

    def ask(self, question: str):
        self.last_question = question
        if self.mode == "unavailable":
            raise ModelUnavailableError("unavailable")
        if self.mode == "tool_error":
            raise CatalogueAgentError("tool error")
        if self.mode == "empty":
            return "No matching books were found for \"software architecture\".", []
        return (
            "I found one software architecture book and it is available.",
            [
                {
                    "id": 1,
                    "title": "Software Architecture in Practice",
                    "author": "Bass",
                    "isbn": "ISBN-ARCH-1",
                    "description": "Architecture foundations.",
                    "availability": True,
                }
            ],
        )


def build_client(service: StubCatalogAgentService) -> TestClient:
    app.dependency_overrides[get_catalog_agent_service] = lambda: service
    return TestClient(app)


def test_post_agent_catalog_returns_answer_and_results() -> None:
    service = StubCatalogAgentService()
    with build_client(service) as client:
        response = client.post(
            "/api/agent/catalog",
            json={
                "question": "Find books about software architecture and check whether they are available"
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert "answer" in body
        assert body["results"][0]["title"] == "Software Architecture in Practice"
        assert service.last_question is not None


def test_post_agent_catalog_zero_matches_returns_empty_results() -> None:
    service = StubCatalogAgentService()
    service.mode = "empty"

    with build_client(service) as client:
        response = client.post(
            "/api/agent/catalog",
            json={"question": "Find books about software architecture"},
        )

        assert response.status_code == 200
        assert response.json()["results"] == []


def test_post_agent_catalog_returns_503_when_provider_unavailable() -> None:
    service = StubCatalogAgentService()
    service.mode = "unavailable"

    with build_client(service) as client:
        response = client.post(
            "/api/agent/catalog",
            json={"question": "Find books about software architecture"},
        )

        assert response.status_code == 503
        assert response.json() == {"detail": "Catalogue agent is unavailable"}


def test_post_agent_catalog_returns_503_when_tool_call_fails() -> None:
    service = StubCatalogAgentService()
    service.mode = "tool_error"

    with build_client(service) as client:
        response = client.post(
            "/api/agent/catalog",
            json={"question": "Find books about software architecture"},
        )

        assert response.status_code == 503
        assert response.json() == {"detail": "Catalogue agent is unavailable"}
