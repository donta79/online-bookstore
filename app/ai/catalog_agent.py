from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool, tool

from app.ai.model_factory import ChatModelFactory, ModelUnavailableError
from app.models.book_models import Book
from app.services.book_service import BookService


class CatalogueAgentError(Exception):
    """Raised when agent tool execution or model invocation fails."""


class CatalogueAgent:
    def __init__(self, book_service: BookService) -> None:
        self._book_service = book_service

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

        tools: list[BaseTool] = [search_books, check_availability]
        answer = self._run_agent(question, tools)

        # Safety loop: if the model skips an availability call, complete it through the tool
        # so results always come from tool observations for every relevant match.
        for book_id in search_result_ids:
            if book_id not in checked_ids:
                check_availability.invoke({"book_id": book_id})

        if not search_result_ids:
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
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a bookstore catalogue assistant.\n"
                    "Always call search_books first.\n"
                    "Then call check_availability for every returned book id.\n"
                    "Answer only from tool observations and do not invent facts.",
                ),
                ("human", "{question}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        # Agent loop: LangChain manages thought/tool/action iterations until final output.
        agent = create_tool_calling_agent(model, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        try:
            response = executor.invoke({"question": question})
        except Exception as exc:  # pragma: no cover - mapped in API tests
            raise CatalogueAgentError("Model invocation failed") from exc

        output = response.get("output")
        if isinstance(output, str):
            return output.strip()
        return ""
