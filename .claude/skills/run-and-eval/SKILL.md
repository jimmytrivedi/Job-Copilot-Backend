---
name: run-and-eval
description: Run the Job Copilot server, ingest the resume into Qdrant, run unit tests, or run the eval suites. Use when asked to start the app, hit the analyze endpoint, re-ingest the corpus, or check whether a prompt/tool change regressed quality.
---

# Running Job Copilot

Everything runs through `uv`. Never `pip install` or activate a venv manually.

## Prerequisites

`.env` must exist at the project root with all keys from `.env.example`. `backend/config.py` reads them at **import time**, so a missing key crashes on startup with `KeyError`, before any request.

```bash
cp .env.example .env   # then fill in
```

## Server

```bash
uv run uvicorn main:app --reload
```

Endpoints:
- `GET /health` — no auth
- `POST /analyze/stream` — requires header `X-API-KEY`, returns `text/event-stream`

SSE events, in order:
```
data: {"stage": "tool", "name": "extract_requirements"}
data: {"stage": "tool", "name": "search_resume"}
data: {"stage": "done", "result": {...Assessment...}}
data: {"stage": "error", "detail": "..."}   # only on AgentLoopExceeded
```

## Hitting the endpoint without a running server

Faster than curl and reuses the loaded `.env`:

```bash
uv run python -c "
from fastapi.testclient import TestClient
from backend.config import settings
import main
c = TestClient(main.app)
r = c.post('/analyze/stream', json={'jd':'Senior Android Developer, Kotlin, Compose.'},
           headers={'X-API-KEY': settings.api_key})
print(r.status_code); print(r.text)
"
```

## Ingest

Chunks `corpus/resume.md`, embeds with Voyage, upserts into the Qdrant `resume` collection.

```bash
uv run python -m scripts.ingest
```

`init_dqrant()` is a **no-op if the collection already exists**. To re-ingest after editing the resume, delete the collection first — otherwise nothing happens and you'll debug stale chunks.

## Unit tests

```bash
uv run pytest -q
```

Only covers pure functions (`chunk_by_char`). Services are not unit-tested — adapters are imported concretely and construct real clients at import, so any service test hits the network.

## Evals — `scripts/evals.py`

Three modes; `run_evals()` selects one by which line is uncommented.

| Function | Checks | Cost |
|---|---|---|
| `rag_relevance_eval` | Retrieved chunks contain an expected keyword | Voyage + Qdrant only |
| `eval_check_tools` | Correct tools fire, in order, ≤2 resume searches | Full agent loop per case |
| `llm_as_judge_check_case` | Opus grades the assessment PASS/FAIL | Full loop + a judge call per case |

Run:
```bash
uv run python -m scripts.evals
```

The `__main__` block at the bottom picks `run_rag_relevance_eval()` or `run_evals()` — edit it to switch.

**The `time.sleep(25)` between cases is load-bearing.** Voyage free tier is 3 RPM; removing it produces `RateLimitError`. `embed_query` also retries 5 times with 25s backoff. A 3-case eval therefore takes minutes, not seconds.

## When to re-run evals

- Changed `SYSTEM_PROMPT` or any tool `description` → `eval_check_tools`
- Changed chunking, embedding model, or the corpus → `rag_relevance_eval`
- Changed the `Assessment` model or scoring guidance → `llm_as_judge_check_case`

## Docker

```bash
docker build -t jobcopilot .
docker run -p 8000:8000 --env-file .env -e PORT=8000 jobcopilot
```
