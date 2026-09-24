from app.ai.direct_prompt import DirectPromptSummarizer
from app.ai.model_factory import ChatModelFactory, ModelUnavailableError


class SummaryService:
    def summarize(self, description: str) -> str:
        try:
            model = ChatModelFactory().create()
        except Exception as exc:  # pragma: no cover - mapped in API tests
            if isinstance(exc, ModelUnavailableError):
                raise
            raise ModelUnavailableError("Model is unavailable") from exc

        summarizer = DirectPromptSummarizer(model)
        return summarizer.summarize(description)
