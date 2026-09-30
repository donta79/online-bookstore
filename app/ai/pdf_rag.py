from collections.abc import Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from app.ai.direct_prompt import _read_message_content


def build_pdf_rag_prompt(question: str, contexts: Sequence[tuple[int, str]]) -> str:
    sources = "\n\n".join(
        f"Page {page_number}:\n{text}" for page_number, text in contexts
    )
    return (
        "Task: Answer the customer's question about the uploaded PDF.\n"
        "Grounding constraint: Use only the supplied retrieved excerpts. Do not use "
        "outside knowledge or infer facts not stated in the excerpts.\n"
        "Insufficient context: If the excerpts do not support an answer, reply exactly: "
        '"I do not have enough information in the uploaded document to answer that."\n'
        "Output: Return only the answer text.\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved excerpts:\n{sources}"
    )


class PdfRagAnswerer:
    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    def answer(self, question: str, contexts: Sequence[tuple[int, str]]) -> str:
        response = self._model.invoke(
            [HumanMessage(content=build_pdf_rag_prompt(question, contexts))]
        )
        return _read_message_content(response.content)
