import os

from langchain_core.language_models.chat_models import BaseChatModel


class ModelUnavailableError(Exception):
    """Raised when the configured chat model cannot be created."""


class ChatModelFactory:
    def create(self) -> BaseChatModel:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

        if provider == "ollama":
            return self._create_ollama_model()

        if provider == "openai":
            return self._create_openai_model()

        raise ModelUnavailableError(f"Unsupported LLM_PROVIDER: {provider}")

    def _create_ollama_model(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        model = os.getenv("OLLAMA_MODEL", "gemma4").strip()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
        if not model:
            raise ModelUnavailableError("OLLAMA_MODEL is not configured")

        return ChatOllama(model=model, base_url=base_url, temperature=0)

    def _create_openai_model(self) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ModelUnavailableError("OPENAI_API_KEY is not configured")

        return ChatOpenAI(model=model, api_key=api_key, temperature=0)
