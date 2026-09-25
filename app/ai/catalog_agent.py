from langchain_core.messages import HumanMessage

from app.ai.model_factory import ChatModelFactory, ModelUnavailableError
from app.models.book_models import Book
from app.services.book_service import BookService


class CatalogueAgentError(Exception):
    """Raised when agent tool execution or model invocation fails."""


class CatalogueAgent:
    def __init__(self, book_service: BookService) -> None:
        self._book_service = book_service

    def answer(self, question: str) -> tuple[str, list[Book]]:
        # Tool 1: search_books(query). The agent always searches first.
        query = _derive_search_query(question)
        try:
            matches = self._book_service.search_books(query)
        except Exception as exc:  # pragma: no cover - API behavior test covers mapping
            raise CatalogueAgentError("Tool call failed: search_books") from exc

        if not matches:
            return f'No matching books were found for "{query}".', []

        collected_results: list[Book] = []
        observations: list[str] = []
        # Tool 2: check_availability(book_id). Check every result found by search.
        for book in matches:
            try:
                available = self._book_service.check_availability(book.id)
            except Exception as exc:  # pragma: no cover - API behavior test covers mapping
                raise CatalogueAgentError("Tool call failed: check_availability") from exc

            observed_book = book.model_copy(update={"availability": available})
            # Result collection: return the exact structured Book observations.
            collected_results.append(observed_book)
            status = "available" if available else "unavailable"
            observations.append(f"- id={book.id}, title={book.title}, availability={status}")

        answer = self._build_grounded_answer(question, query, observations)
        return answer, collected_results

    def _build_grounded_answer(self, question: str, query: str, observations: list[str]) -> str:
        try:
            model = ChatModelFactory().create()
        except Exception as exc:  # pragma: no cover - mapped by API
            if isinstance(exc, ModelUnavailableError):
                raise
            raise CatalogueAgentError("Could not initialize configured model") from exc

        prompt = build_catalog_agent_prompt(question, query, observations)
        try:
            response = model.invoke([HumanMessage(content=prompt)])
        except Exception as exc:  # pragma: no cover - mapped by API
            raise CatalogueAgentError("Model invocation failed") from exc

        content = _read_message_content(response.content)
        return content or "I checked the catalogue but could not generate a detailed answer."


def build_catalog_agent_prompt(question: str, query: str, observations: list[str]) -> str:
    # Grounding rule: the model can only use the tool observations listed below.
    observation_block = "\n".join(observations)
    return (
        "You are a bookstore catalogue assistant.\n"
        "You must answer only using the tool observations provided.\n"
        "Do not invent books, IDs, or availability.\n"
        "If any information is missing, say so clearly.\n"
        "Respond in concise customer-friendly prose.\n\n"
        f"Original customer question: {question}\n"
        f"Search query used: {query}\n"
        "Tool observations:\n"
        f"{observation_block}\n\n"
        "Final answer:"
    )


def _derive_search_query(question: str) -> str:
    normalized = question.strip()
    if not normalized:
        return normalized

    lowercase = normalized.lower()
    about_index = lowercase.find("about ")
    if about_index >= 0:
        start = about_index + len("about ")
        stop = len(normalized)
        for marker in (" and ", " with "):
            marker_index = lowercase.find(marker, start)
            if marker_index >= 0:
                stop = min(stop, marker_index)
        query = normalized[start:stop].strip(" .!?")
        if query:
            return query

    first_quote = normalized.find('"')
    if first_quote >= 0:
        second_quote = normalized.find('"', first_quote + 1)
        if second_quote > first_quote + 1:
            return normalized[first_quote + 1 : second_quote].strip()

    return normalized


def _read_message_content(content: str | list[dict] | list[str]) -> str:
    if isinstance(content, str):
        return content.strip()

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
            continue
        if isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)

    return " ".join(parts).strip()
