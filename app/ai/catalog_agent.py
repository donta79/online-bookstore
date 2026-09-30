from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool, tool

from app.ai.mcp_client import DocsLookupUnavailableError, MicrosoftLearnMCPClient
from app.ai.model_factory import ChatModelFactory, ModelUnavailableError
from app.models.book_models import Book
from app.services.book_service import BookService


class CatalogueAgentError(Exception):
    """Raised when agent tool execution or model invocation fails."""


class CatalogueAgent:
    def __init__(
        self,
        book_service: BookService,
        docs_client: MicrosoftLearnMCPClient | None = None,
    ) -> None:
        self._book_service = book_service
        # The docs client is optional and its unavailability must never break
        # catalogue-only answers, so it is never allowed to raise CatalogueAgentError.
        self._docs_client = docs_client or MicrosoftLearnMCPClient()

    def answer(self, question: str) -> tuple[str, list[Book]]:
        observed_books: dict[int, Book] = {}
        search_result_ids: list[int] = []
        checked_ids: set[int] = set()
        last_query = question.strip()

        # Tool 1: search_books(query). The agent must call this first.
        @tool
        def search_books(query: str) -> list[dict[str, Any]]:
            """Search catalogue books by title, author, or description."""

            nonlocal last_query
            last_query = query
            try:
                books = self._book_service.search_books(query)
            except Exception as exc:
                raise CatalogueAgentError("Tool call failed: search_books") from exc

            search_result_ids.clear()
            for book in books:
                search_result_ids.append(book.id)
                observed_books[book.id] = book

            return [book.model_dump() for book in books]

        # Tool 2: check_availability(book_id). The agent should call this for every found result.
        @tool
        def check_availability(book_id: int) -> bool:
            """Check whether a book is currently available by id."""

            try:
                available = self._book_service.check_availability(book_id)
            except Exception as exc:
                raise CatalogueAgentError("Tool call failed: check_availability") from exc

            checked_ids.add(book_id)
            if book_id in observed_books:
                observed_books[book_id] = observed_books[book_id].model_copy(
                    update={"availability": available}
                )
            return available

        docs_used = False

        # Tool 3: lookup_docs(query). Optional; only relevant for technical/how-to
        # questions. Failures are swallowed here so a down Microsoft Learn MCP
        # server never turns a catalogue-answerable question into an error.
        @tool
        def lookup_docs(query: str) -> str:
            """Look up Microsoft Learn documentation for a technical or how-to question."""

            nonlocal docs_used
            docs_used = True
            try:
                return self._docs_client.lookup_docs(query)
            except DocsLookupUnavailableError:
                return "Documentation lookup is currently unavailable right now."

        tools: list[BaseTool] = [search_books, check_availability, lookup_docs]
        answer = self._run_agent(question, tools)

        # Safety loop: if the model skips an availability call, complete it through the tool
        # so results always come from tool observations for every relevant match.
        for book_id in search_result_ids:
            if book_id not in checked_ids:
                check_availability.invoke({"book_id": book_id})

        if not search_result_ids:
            # A technical question may have no catalogue matches while still
            # having a valid documentation-grounded answer; only fall back to
            # the "no matching books" message when docs were not the source.
            if docs_used and answer:
                return answer, []
            return f'No matching books were found for "{last_query}".', []

        # Result collection: return the exact structured Book values collected by tools.
        results = [observed_books[book_id] for book_id in search_result_ids]
        if not answer:
            answer = "I checked the catalogue and listed the matching books with their availability."
        return answer, results

    def _run_agent(self, question: str, tools: list[BaseTool]) -> str:
        try:
            model = ChatModelFactory().create()
        except Exception as exc:  # pragma: no cover - mapped in API tests
            if isinstance(exc, ModelUnavailableError):
                raise
            raise CatalogueAgentError("Could not initialize configured model") from exc

        # Grounding instructions keep the final answer tied strictly to tool outputs.
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=(
                "You are a bookstore catalogue assistant.\n"
                "For catalogue questions (about books, availability, or the store's inventory), "
                "always call search_books first, then call check_availability for every "
                "returned book id.\n"
                "For technical or how-to questions about a subject (e.g. programming, "
                "frameworks, or how something works), call lookup_docs with the technical "
                "topic and ground your answer in its result.\n"
                "A question may need both tools; call whichever apply.\n"
                "Answer only from tool observations and do not invent facts. If lookup_docs "
                "reports it is unavailable, say so plainly instead of guessing."
            ),
        )

        try:
            # Agent loop: LangChain manages tool iterations until final answer output.
            response = agent.invoke({"messages": [{"role": "user", "content": question}]})
        except Exception as exc:  # pragma: no cover - mapped in API tests
            raise CatalogueAgentError("Model invocation failed") from exc

        messages = response.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                if isinstance(message, AIMessage):
                    return _read_message_content(message)
        return ""


def _read_message_content(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content.strip()

    parts: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)

    return " ".join(parts).strip()
