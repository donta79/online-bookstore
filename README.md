# online-bookstore

Set `BOOKSTORE_DATABASE_PATH` to choose the SQLite database file. It defaults to
`data/bookstore.db`; copy `.env.example` for local configuration.

## PDF questions

Upload a text-based PDF from the browser, then ask a question about it. The active
document, extracted text, retrieval index, and answers exist only in application
memory and are discarded when the process stops. Configure the AI provider with
the `LLM_PROVIDER`, Ollama, or OpenAI settings in `.env.example`.