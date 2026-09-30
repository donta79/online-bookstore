from langchain_core.messages import AIMessage

import app.ai.catalog_agent as catalog_agent_module
from app.ai.catalog_agent import CatalogueAgent
from app.ai.mcp_client import DocsLookupUnavailableError
from app.models.book_models import Book


class FakeBookService:
    def __init__(self, books: list[Book]) -> None:
        self._books = {book.id: book for book in books}

    def search_books(self, query: str) -> list[Book]:
        return list(self._books.values())

    def check_availability(self, book_id: int) -> bool:
        return self._books[book_id].availability


class FakeDocsClient:
    def __init__(self, text: str | None = None, error: Exception | None = None) -> None:
        self._text = text
        self._error = error
        self.last_query: str | None = None

    def lookup_docs(self, query: str) -> str:
        self.last_query = query
        if self._error is not None:
            raise self._error
        return self._text or ""


class FakeAgent:
    """Stands in for langchain's create_agent, invoking a fixed sequence of tools."""

    def __init__(self, tools, tool_calls, final_answer: str) -> None:
        self._tools = {t.name: t for t in tools}
        self._tool_calls = tool_calls
        self._final_answer = final_answer

    def invoke(self, _input):
        for tool_name, tool_args in self._tool_calls:
            self._tools[tool_name].invoke(tool_args)
        return {"messages": [AIMessage(content=self._final_answer)]}


def _patch_model_factory(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_agent_module.ChatModelFactory, "create", lambda self: object()
    )


def _patch_create_agent(monkeypatch, tool_calls, final_answer: str) -> None:
    def _fake_create_agent(model, tools, system_prompt):
        return FakeAgent(tools, tool_calls, final_answer)

    monkeypatch.setattr(catalog_agent_module, "create_agent", _fake_create_agent)


def test_lookup_docs_tool_is_wired_and_folded_into_answer(monkeypatch) -> None:
    _patch_model_factory(monkeypatch)
    docs_client = FakeDocsClient(text="Dependency injection is FastAPI's way of providing values.")
    _patch_create_agent(
        monkeypatch,
        tool_calls=[("lookup_docs", {"query": "FastAPI dependency injection"})],
        final_answer="Dependency injection is FastAPI's way of providing values.",
    )

    agent = CatalogueAgent(FakeBookService([]), docs_client=docs_client)
    answer, results = agent.answer("What is FastAPI dependency injection?")

    assert docs_client.last_query == "FastAPI dependency injection"
    assert answer == "Dependency injection is FastAPI's way of providing values."
    assert results == []


def test_docs_unavailable_degrades_gracefully_without_error(monkeypatch) -> None:
    _patch_model_factory(monkeypatch)
    docs_client = FakeDocsClient(error=DocsLookupUnavailableError("down"))
    _patch_create_agent(
        monkeypatch,
        tool_calls=[("lookup_docs", {"query": "FastAPI dependency injection"})],
        final_answer="Documentation lookup is currently unavailable right now.",
    )

    agent = CatalogueAgent(FakeBookService([]), docs_client=docs_client)
    answer, results = agent.answer("What is FastAPI dependency injection?")

    assert "unavailable" in answer.lower()
    assert results == []


def test_catalogue_only_question_behaves_as_before(monkeypatch) -> None:
    _patch_model_factory(monkeypatch)
    book = Book(
        id=1,
        title="Software Architecture in Practice",
        author="Bass",
        isbn="ISBN-ARCH-1",
        description="Architecture foundations.",
        availability=True,
    )
    docs_client = FakeDocsClient()
    _patch_create_agent(
        monkeypatch,
        tool_calls=[
            ("search_books", {"query": "software architecture"}),
            ("check_availability", {"book_id": 1}),
        ],
        final_answer="I found one software architecture book and it is available.",
    )

    agent = CatalogueAgent(FakeBookService([book]), docs_client=docs_client)
    answer, results = agent.answer("Find books about software architecture")

    assert docs_client.last_query is None
    assert answer == "I found one software architecture book and it is available."
    assert len(results) == 1
    assert results[0].title == "Software Architecture in Practice"


def test_catalogue_only_zero_matches_returns_fallback_message(monkeypatch) -> None:
    _patch_model_factory(monkeypatch)
    docs_client = FakeDocsClient()
    _patch_create_agent(
        monkeypatch,
        tool_calls=[("search_books", {"query": "software architecture"})],
        final_answer="",
    )

    agent = CatalogueAgent(FakeBookService([]), docs_client=docs_client)
    answer, results = agent.answer("Find books about software architecture")

    assert answer == 'No matching books were found for "software architecture".'
    assert results == []
