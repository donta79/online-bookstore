"""Client wrapper around the Microsoft Learn MCP server.

The endpoint is environment-configured (never hardcoded) and tools are
discovered dynamically from the remote server, since the MCP server owns its
own tool catalogue and schema. Any failure to reach or use the server is
caught here so catalogue-only answers never depend on it being available.
"""

import asyncio
import os
from typing import Any

from langchain_core.tools import BaseTool


class DocsLookupUnavailableError(Exception):
    """Raised when the Microsoft Learn MCP server cannot be used."""


class MicrosoftLearnMCPClient:
    """Discovers and calls tools on the Microsoft Learn Streamable HTTP MCP server."""

    def __init__(self) -> None:
        self._endpoint = os.getenv("MCP_LEARN_ENDPOINT", "").strip()

    def lookup_docs(self, query: str) -> str:
        """Look up Microsoft Learn documentation for a technical query.

        Returns the raw tool output as text. Raises DocsLookupUnavailableError
        if the server is not configured, unreachable, or exposes no usable tool.
        """

        if not self._endpoint:
            raise DocsLookupUnavailableError("MCP_LEARN_ENDPOINT is not configured")

        try:
            return asyncio.run(self._lookup_docs_async(query))
        except DocsLookupUnavailableError:
            raise
        except Exception as exc:
            raise DocsLookupUnavailableError(
                "Microsoft Learn MCP server is unavailable"
            ) from exc

    async def _lookup_docs_async(self, query: str) -> str:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient(
            {
                "microsoft_learn": {
                    "transport": "streamable_http",
                    "url": self._endpoint,
                }
            }
        )

        # Dynamic discovery: the remote server defines its own tool names and
        # schemas, so pick the first documentation/search-style tool exposed
        # rather than assuming a fixed tool name.
        tools: list[BaseTool] = await client.get_tools()
        docs_tool = _select_docs_tool(tools)
        if docs_tool is None:
            raise DocsLookupUnavailableError(
                "Microsoft Learn MCP server exposed no usable tool"
            )

        result = await docs_tool.ainvoke({"query": query})
        return _stringify(result)


def _select_docs_tool(tools: list[BaseTool]) -> BaseTool | None:
    if not tools:
        return None

    for candidate in tools:
        name = candidate.name.lower()
        if "search" in name or "doc" in name or "fetch" in name:
            return candidate

    return tools[0]


def _stringify(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        parts = []
        for item in result:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return str(result)
