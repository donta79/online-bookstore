from langchain_core.tools import tool

from app.ai.mcp_client import (
    DocsLookupUnavailableError,
    MicrosoftLearnMCPClient,
    _select_docs_tool,
    _stringify,
)


def test_lookup_docs_raises_when_endpoint_disabled(monkeypatch) -> None:
    monkeypatch.setenv("MCP_LEARN_ENDPOINT", "")
    client = MicrosoftLearnMCPClient()

    try:
        client.lookup_docs("FastAPI dependency injection")
        assert False, "expected DocsLookupUnavailableError"
    except DocsLookupUnavailableError:
        pass


def test_default_endpoint_is_used_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("MCP_LEARN_ENDPOINT", raising=False)
    client = MicrosoftLearnMCPClient()

    assert client._endpoint == "https://learn.microsoft.com/api/mcp"


def test_lookup_docs_wraps_connection_failures(monkeypatch) -> None:
    monkeypatch.setenv("MCP_LEARN_ENDPOINT", "https://learn.microsoft.com/mcp")
    client = MicrosoftLearnMCPClient()

    async def _boom(self, query: str) -> str:
        raise RuntimeError("connection refused")

    monkeypatch.setattr(MicrosoftLearnMCPClient, "_lookup_docs_async", _boom)

    try:
        client.lookup_docs("FastAPI dependency injection")
        assert False, "expected DocsLookupUnavailableError"
    except DocsLookupUnavailableError:
        pass


def test_select_docs_tool_prefers_search_or_doc_named_tool() -> None:
    @tool
    def unrelated_tool(query: str) -> str:
        """An unrelated tool."""
        return query

    @tool
    def microsoft_docs_search(query: str) -> str:
        """Search Microsoft Learn documentation."""
        return query

    selected = _select_docs_tool([unrelated_tool, microsoft_docs_search])
    assert selected is microsoft_docs_search


def test_select_docs_tool_falls_back_to_first_tool_when_no_match() -> None:
    @tool
    def alpha(query: str) -> str:
        """Alpha tool."""
        return query

    @tool
    def beta(query: str) -> str:
        """Beta tool."""
        return query

    selected = _select_docs_tool([alpha, beta])
    assert selected is alpha


def test_select_docs_tool_returns_none_when_no_tools() -> None:
    assert _select_docs_tool([]) is None


def test_stringify_handles_str_list_and_other() -> None:
    assert _stringify("plain text") == "plain text"
    assert _stringify([{"text": "one"}, "two"]) == "one\ntwo"
    assert _stringify({"nested": True}) == "{'nested': True}"
