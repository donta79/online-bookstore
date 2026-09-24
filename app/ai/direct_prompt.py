import re

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


def build_summary_prompt(description: str) -> str:
    return (
        "Task: Summarize the book description for a customer deciding whether to read it.\n"
        "Audience: A bookstore customer who wants a quick overview.\n"
        "Length: Exactly two concise sentences.\n"
        "Grounding constraint: Use only facts from the provided description and do not add any external details.\n"
        "Output: Return only the summary text.\n\n"
        f"Book description:\n{description}"
    )


class DirectPromptSummarizer:
    # This uses direct prompting intentionally: one model call with a constrained prompt
    # for deterministic request/response behavior, without tools, memory, or side effects.
    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    def summarize(self, description: str) -> str:
        prompt = build_summary_prompt(description)
        response = self._model.invoke([HumanMessage(content=prompt)])
        content = _read_message_content(response.content)
        return _to_two_sentences(content)


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


def _to_two_sentences(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    trimmed = [sentence.strip() for sentence in sentences if sentence.strip()]
    if len(trimmed) <= 2:
        return " ".join(trimmed)

    return " ".join(trimmed[:2])
