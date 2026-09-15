---
name: architecture
description: Layering rules for this codebase — which layer a new function, class, or file belongs in, and which imports are allowed. Use when adding a file, deciding where code goes, reviewing a change for layer violations, or when the user asks "where should this live?".
---

# Job Copilot architecture

Layered Python service. Dependencies point **one way only**:

```
api  →  services  →  adapters  →  config
              ↘  domain  ↙
                  llm
```

`domain` and `llm` are leaves — they import nothing from other layers (`domain` may import `config` for nothing today; keep it that way).

## Layers

### `backend/api/` — HTTP transport
`routes.py` `deps.py` `sse.py`

The only layer allowed to import `fastapi`. Owns status codes, SSE framing, auth dependencies, request/response translation.

- Translates domain exceptions → HTTP responses
- Never contains business logic

### `backend/services/` — use cases
`analyzer.py` `retrieval.py` `tool_runner.py` `evaluation.py`

Orchestration. Calls adapters, applies rules, raises domain errors.

- MUST NOT import `fastapi` or raise `HTTPException`
- MUST NOT construct vendor SDK clients — import them from `adapters/`
- MUST NOT emit transport formats (no `data: ...\n\n`) — yield plain dicts

### `backend/adapters/` — vendor boundaries
`anthropic_llm.py` `qdrant_store.py` `voyage_embedder.py` `tavily_search.py` `mcp_filesystem.py`

One file per external system. Named by **role**, never by SDK.

- Exposes what the vendor *does* (`embed_documents(texts)`), not what the app *needs* (`embed_the_resume()`)
- Holds the single client instance for that vendor
- Imports only `config`
- Pure logic that happens to sit near a vendor call (chunking, joining, retries-as-policy) belongs in `services/`

### `backend/domain/` — contracts
`models.py` `errors.py`

Pydantic models and exception types. Zero third-party imports beyond pydantic.

### `backend/llm/` — prompt assets
`prompts.py` `tool_specs.py`

Every prompt string and every Claude tool declaration + JSON schema. No API calls here — declarations only; the matching executor goes in `services/tool_runner.py`.

### `backend/config.py`
The only place that reads `os.environ` or calls `load_dotenv()`. Also owns `PROJECT_ROOT`, model IDs, and tuning constants. No module counts its own directory levels.

## Placement decision

| What you're adding | Goes in |
|---|---|
| New HTTP endpoint | `api/routes.py` |
| New Claude tool | declaration → `llm/tool_specs.py`, executor → `services/tool_runner.py` |
| New prompt text | `llm/prompts.py` |
| Wrapper around a new SaaS/API | new file in `adapters/` |
| Multi-step flow across adapters | `services/` |
| Pure function (string/math/parsing) | `services/`, and add a test |
| New env var or constant | `config.py` |
| New error type | `domain/errors.py` |

## Verifying a change

```bash
# no web framework below api/
grep -rn "fastapi" backend/services backend/adapters backend/domain backend/llm

# env access only in config
grep -rn "os.environ\|load_dotenv" backend/ | grep -v backend/config.py

# no stray prints
grep -rn "print(" backend/

uv run pytest -q
uv run python -c "import main; print('OK')"
```

All four greps should return nothing.

## Known deliberate gaps

- No `Protocol` ports; services import concrete adapters. Decided against — only one implementation of each, and unit-testing services with fakes was explicitly out of scope.
- Adapter clients are constructed at import time, so importing any service needs real env vars.
- `README.md` is a build journal and still names pre-refactor files. Not current documentation.
