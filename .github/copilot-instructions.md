# Coding-agent instructions

## Current repository state

This repository is the output of Lab 2. It contains project documentation and collaboration files, but no application code yet.

## Lab 3 target

- Python and FastAPI backend
- Pydantic request and response models
- Plain HTML, CSS, and JavaScript frontend
- In-memory catalogue only
- pytest for deterministic tests
- LangChain for the agent feature
- Ollama `gemma4` or OpenAI `gpt-5.4-mini` for AI features

## Architecture

When scaffolding begins, use these responsibilities:

- `app/api/`: HTTP routes
- `app/services/`: application and business logic
- `app/repositories/`: data access abstraction and in-memory repository
- `app/models/`: Pydantic models
- `app/ai/`: model factory, direct prompting, and agent code
- `app/static/`: browser UI
- `tests/`: automated tests

Routes must delegate catalogue logic to a service. Routes obtain services through FastAPI `Depends`; do not construct repositories in route handlers.

## Working rules

- Read the selected GitHub Issue before proposing code.
- Restate requirements, assumptions, affected files, implementation steps, and tests before editing.
- Wait for human approval of the plan.
- Implement only one issue on the current branch.
- Add or update tests for each deterministic feature.
- Do not add a database, ORM, authentication, authorization, payments, or deployment.
- Never add credentials or commit `.env`.
- Do not change unrelated files.
