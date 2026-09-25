from app.ai.catalog_agent import CatalogueAgent
from app.models.book_models import Book
from app.services.book_service import BookService


class CatalogAgentService:
    def __init__(self, book_service: BookService) -> None:
        self._agent = CatalogueAgent(book_service)

    def ask(self, question: str) -> tuple[str, list[Book]]:
        return self._agent.answer(question)
