# online-bookstore

Set `BOOKSTORE_DATABASE_PATH` to choose the SQLite database file. It defaults to
`data/bookstore.db`; copy `.env.example` for local configuration.

## PDF questions

Upload a text-based PDF from the browser, then ask a question about it. The active
document, extracted text, retrieval index, and answers exist only in application
memory and are discarded when the process stops. Configure the AI provider with
the `LLM_PROVIDER`, Ollama, or OpenAI settings in `.env.example`.

## Catalogue agent documentation lookups

The catalogue agent (`POST /api/agent/catalog`) can call `lookup_docs(query)` for
technical or how-to questions, in addition to its catalogue tools. This tool
connects to a Microsoft Learn MCP server over Streamable HTTP, with the endpoint
configured via `MCP_LEARN_ENDPOINT` in `.env.example` (never hardcoded) and its
tools discovered dynamically. Documentation content is folded into the existing
`answer` field; the `results` field always stays catalogue-only. If the MCP
server is unset or unreachable, the agent notes the limitation and still answers
catalogue-answerable questions normally.