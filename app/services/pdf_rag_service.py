import io
import re
from dataclasses import dataclass

from pypdf import PdfReader

from app.ai.model_factory import ChatModelFactory, ModelUnavailableError
from app.ai.pdf_rag import PdfRagAnswerer
from app.models.pdf_rag_models import (
    PdfRagDocumentResponse,
    PdfRagQuestionResponse,
    PdfRagSource,
)

INSUFFICIENT_CONTEXT_ANSWER = (
    "I do not have enough information in the uploaded document to answer that."
)
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 120
_MAX_SOURCES = 3
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "what",
        "when",
        "where",
        "which",
        "who",
        "with",
    }
)


class PdfDocumentValidationError(Exception):
    """Raised when an uploaded document cannot be used for retrieval."""


class PdfDocumentNotFoundError(Exception):
    """Raised when a question is asked before any document is indexed."""


@dataclass(frozen=True)
class IndexedChunk:
    page_number: int
    text: str


@dataclass(frozen=True)
class IndexedDocument:
    name: str
    page_count: int
    chunks: tuple[IndexedChunk, ...]


class PdfRagService:
    def __init__(self) -> None:
        self._active_document: IndexedDocument | None = None

    def index_document(
        self, filename: str | None, content_type: str | None, content: bytes
    ) -> PdfRagDocumentResponse:
        self._validate_upload(filename, content_type, content)
        try:
            reader = PdfReader(io.BytesIO(content))
            chunks = tuple(
                IndexedChunk(page_number=page_number, text=chunk)
                for page_number, page in enumerate(reader.pages, start=1)
                for chunk in _split_text(page.extract_text() or "")
            )
        except Exception as exc:
            raise PdfDocumentValidationError(
                "The uploaded file is not a readable PDF"
            ) from exc

        if not chunks:
            raise PdfDocumentValidationError(
                "The PDF does not contain extractable text"
            )

        document = IndexedDocument(
            name=filename,
            page_count=len(reader.pages),
            chunks=chunks,
        )
        self._active_document = document
        return PdfRagDocumentResponse(
            document_name=document.name,
            page_count=document.page_count,
            chunk_count=len(document.chunks),
        )

    def answer_question(self, question: str) -> PdfRagQuestionResponse:
        document = self._active_document
        if document is None:
            raise PdfDocumentNotFoundError()

        chunks = _retrieve_relevant_chunks(question, document.chunks)
        if not chunks:
            return PdfRagQuestionResponse(
                answer=INSUFFICIENT_CONTEXT_ANSWER,
                sources=[],
                insufficient_context=True,
            )

        try:
            answer = PdfRagAnswerer(ChatModelFactory().create()).answer(
                question,
                [(chunk.page_number, chunk.text) for chunk in chunks],
            )
        except Exception as exc:
            if isinstance(exc, ModelUnavailableError):
                raise
            raise ModelUnavailableError("Model is unavailable") from exc

        return PdfRagQuestionResponse(
            answer=answer or INSUFFICIENT_CONTEXT_ANSWER,
            sources=[
                PdfRagSource(excerpt=chunk.text, page_number=chunk.page_number)
                for chunk in chunks
            ],
            insufficient_context=False,
        )

    @staticmethod
    def _validate_upload(
        filename: str | None, content_type: str | None, content: bytes
    ) -> None:
        if not filename or not filename.lower().endswith(".pdf"):
            raise PdfDocumentValidationError("Upload a PDF file")
        if content_type not in {"application/pdf", "application/x-pdf"}:
            raise PdfDocumentValidationError("Upload a PDF file")
        if not content.startswith(b"%PDF-"):
            raise PdfDocumentValidationError("Upload a valid PDF file")


def _split_text(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + _CHUNK_SIZE, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = end - _CHUNK_OVERLAP
    return chunks


def _retrieve_relevant_chunks(
    question: str, chunks: tuple[IndexedChunk, ...]
) -> list[IndexedChunk]:
    question_terms = {
        term
        for term in re.findall(r"\b\w{2,}\b", question.lower())
        if term not in _STOP_WORDS
    }
    scored_chunks = [
        (
            len(question_terms & set(re.findall(r"\b\w{2,}\b", chunk.text.lower()))),
            index,
            chunk,
        )
        for index, chunk in enumerate(chunks)
    ]
    return [
        chunk
        for score, _, chunk in sorted(
            scored_chunks, key=lambda result: (-result[0], result[1])
        )
        if score > 0
    ][:_MAX_SOURCES]
