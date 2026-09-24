import os

from langchain_core.language_models.chat_models import BaseChatModel


class ModelUnavailableError(Exception):
    """Raised when the configured chat model cannot be created."""


class ChatModelFactory:
    """Builds the configured chat model for the direct-prompt summary flow.

    The provider switch is environment-driven so the same code path works for:
    - local Ollama testing with gemma4
    - hosted OpenAI usage with gpt-5.4-mini
    """

    def create(self) -> BaseChatModel:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

        if provider == "ollama":
            return self._create_ollama_model()

        if provider == "openai":
            return self._create_openai_model()

        raise ModelUnavailableError(f"Unsupported LLM_PROVIDER: {provider}")

    def _create_ollama_model(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        # Keep defaults aligned with .env.example so local development works
        # without extra configuration when Ollama is available.
        model = os.getenv("OLLAMA_MODEL", "gemma4").strip()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
        if not model:
            raise ModelUnavailableError("OLLAMA_MODEL is not configured")

        return ChatOllama(model=model, base_url=base_url, temperature=0)

    def _create_openai_model(self) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        # OpenAI calls require an API key; map missing credentials to the
        # shared model-unavailable error so the API can consistently return 503.
        model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ModelUnavailableError("OPENAI_API_KEY is not configured")

        return ChatOpenAI(model=model, api_key=api_key, temperature=0)
