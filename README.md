# Job Copilot

Analyzes a job description against my resume using Claude, RAG over Qdrant, and tool calling.
Built checkpoint by checkpoint — the journal below is the actual build log.

Local Server
uv run uvicorn main:app --reload
---

## Architecture

```
                         main.py
                            │
                            ▼
  ┌──────────────────────────────────────────────────────────┐
  │  api/        routes · deps · sse                         │  FastAPI, auth, SSE framing
  └──────────────────────────────────────────────────────────┘
                            │
                            ▼
  ┌──────────────────────────────────────────────────────────┐
  │  services/   analyzer · retrieval                        │  agent loop, orchestration
  │              tool_runner · evaluation                    │
  └──────────────────────────────────────────────────────────┘
                            │
                            ▼
  ┌──────────────────────────────────────────────────────────┐
  │  adapters/   anthropic_llm · qdrant_store                │  one file per vendor
  │              voyage_embedder · tavily_search             │
  │              mcp_filesystem                              │
  └──────────────────────────────────────────────────────────┘
                            │
                            ▼
  ┌──────────────────────────────────────────────────────────┐
  │  config.py   env vars · model IDs · PROJECT_ROOT         │
  └──────────────────────────────────────────────────────────┘

  domain/   models · errors      ← contracts, used by every layer
  llm/      prompts · tool_specs ← prompt text and tool declarations
```

**Rule: arrows point one way.** No FastAPI below `api/`, no vendor SDK above `adapters/`,
and `os.environ` only in `config.py`.

| Layer | Holds | Must not |
| --- | --- | --- |
| `api/` | routes, API-key dependency, SSE framing | contain business logic |
| `services/` | agent loop, retrieval flow, tool execution, judging | import `fastapi` or build vendor clients |
| `adapters/` | one client per external system | know anything about the app's use cases |
| `domain/` | Pydantic models, exception types | import anything but pydantic |
| `llm/` | prompt strings, tool schemas + declarations | make API calls |
| `config.py` | every env var, model ID, path, constant | — |

---

## Skills

Project skills live in `.claude/skills/` and load automatically in Claude Code.

| Skill | Use it when |
| --- | --- |
| `architecture` | Deciding where a new file or function belongs, or checking a change for layer violations |
| `add-tool` | Adding or changing a Claude tool — covers all five places it must be registered |
| `run-and-eval` | Starting the server, re-ingesting the resume, running pytest or the eval suites |
| `prompt-changes` | Editing any prompt — brace escaping, cache invalidation, structured-output pairing |

---

## Build journal

## Checkpoint 0 — Environment ready
- Created project
- Created .env file and added API keys (Anthropic, Voyage AI, Qdrant Key, Qdrant URL)

  [Voyage AI creates embedding models that convert text into vectors]

  [Qdrant is a Vector Database, it is required to store the embeddings created by Voyage AI]

  [Qdrant URL and key to access DB]

- Added .env file in .gitignore
- Install / Verify Node.js [`node --version`]
- Create root level folder to put resume — `corpus/resume.md`
- Need to install packages: Local env

Local env setup commands:

```bash
uv init
uv venv
source .venv/bin/activate
uv add fastapi "uvicorn[standard]"
```

- Delete src folder, so that we can run / root everything from main.py
- Add files in Git
- gitignore: uv.lock, .env

Go to pyproject.toml and delete these 2 blocks from the bottom, because we'll run this from main.py:

```toml
[project.scripts]
jobcopilot = "jobcopilot:main"

[build-system]
requires = ["uv_build>=0.12.5,<0.13.0"]
build-backend = "uv_build"
```

## Checkpoint 1 — FastAPI skeleton alive

Update main.py, so that you can run the server:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

Command: `uvicorn main:app --reload`

Output: Server is running

## Checkpoint 2 — Claude responds to a real request

- Create post request `/analyze`
- Create `backend/models.py`
- Create class

```python
from pydantic import BaseModel

class Assessment(BaseModel):
    jd: str
    resume: str
```

Write a post function with return type of: `@app.post("/analyze")`

Create claude_client to make use of the Claude API:

```bash
uv add anthropic         # To get Anthropic packages
uv add python-dotenv     # To directly read API keys from .env file
```

```python
import anthropic
import os

from dotenv import load_dotenv

load_dotenv()  # Reads the .env file and loads its variables into os.environ
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-6",  # List of Model IDs: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

After writing the basic Claude client setup, print it and run the command below:

```bash
uv run claude_client.py
```

Working fine, got a response from Claude: *Hello! How are you doing? Is there something I can help you with today? 😊*

Now, the next task is to use the Claude API to assess the JD with the resume, which means inside main.py we should call the claude_client function:

```python
@app.post("/analyze")
def analyze(assessment: Assessment) -> Assessment:
    result = analyze_with_claude(f"JD: {assessment.jd}\nResume: {assessment.resume}")
    return {"result": result}
```

Got status code 200 with an unformatted response. But it is analyzing. Need structure / schema improvement.

To improve accuracy, now add a system prompt, so create prompts.py:

```python
system=SYSTEM_PROMPT
```

## Checkpoint 3 — Structured output

To provide input and output format with JSON:

1. Update Assessment class — rename to `AnalyzeRequest`: this is for input
2. Create a new class inside models.py — `Assessment` — this is for output

   ```python
   match_score: int
   strengths: list[str]
   gaps: list[str]
   verdict: str
   ```

3. Update system prompt and define Assessment class fields
4. Need to add a JSON parser

We're getting a response based on JSON.

## Checkpoint 4 — RAG

Goal: Instead of sending the resume as a prompt, use it from `corpus/resume.md`. That means it needs to be uploaded to Qdrant DB (Vector DB) using Voyage AI.

- Command: `uv add voyageai`
- Create voyage_client

```python
client = voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY"))
result = client.embed(texts=["Hello World"], model="voyage-4-large")
print(result)
```

Able to convert from text to embeddings:

```bash
uv run voyage_client.py
```
```
<voyageai.object.embeddings.EmbeddingsObject object at 0x109abef90>
```

Now need to store into Qdrant DB:

```bash
uv add qdrant-client
```

- Create `qdrant_client_db.py`
- Create client object, new collection and store it using `client.upsert`
- Once this succeeds, add long text, break into chunks and store inside Qdrant, chunk wise: `get_embeddings_by_chunks()`

Next: need to store the resume instead of manual dummy text.

Reading `corpus/resume.md`:

```python
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(base, "corpus/resume.md"), "r") as f:
    text = f.read()
```

and passing text: `chunk_by_char(text)`

**Question:** Am I pasting the entire resume with every request?

**Answer:** Need code correction first.

1. Inside rag.py — create a new function `insert_vectors`, and the insertion logic we were doing inside qdrant_client moves into `insert_vectors()`
2. Need to write a retrieval function, which will retrieve data from Qdrant top-K chunks and append to the Claude query
3. Create rag.py and write the retrieve function with query params
4. To retrieve data based on query params, we should convert the query to embeddings and then pass to Qdrant
5. Receive request (jd only) → retrieve chunks from Qdrant → build prompt with jd + chunks → call Claude → return

Output: Resume is now not attached in every request.

## Checkpoint 5 — Tool calling

Why we need tool calling: In our current app, we manually do retrieval — we always call Qdrant before calling Claude, regardless of whether it's needed.
With tool calling, you'd instead give Claude a `search_resume(query)` tool, and Claude itself decides when to call it, what query to search for,
and even whether to search multiple times. The control shifts from your code to the model, making the system more flexible and agent-like.

- Create tool — `tools.py` — `search_resume()`
- Create `schemas.py` to provide inside tools. Tools need schemas
- Provide tool access to Claude
- Claude is calling the tool. Now need to handle Claude's response: `ToolUseBlock`
- Claude is using the tool and we're getting 200.

## Checkpoint 6 — Agent loop

Tailored bullets support — means rewrite resume bullet points based on JD.

Rule: tailored bullets must only mention skills that appear in the candidate's resume content.

- Add more tools
- Agent loop safety guard — `MAX_ITERATIONS = 5`
- Updated prompt and many more corrections

## Checkpoint 7 — MCP

The Claude JD analysis, we're going to write in one file.
We're writing this file through MCP instead of normal file functionality.
Our logic should write / touch the file only in the allowed directory, anywhere else it should throw an error.
Python code is the client and the file system is the server in this case.

1. Install MCP server as a filesystem with this command: `npm install -g @modelcontextprotocol/server-filesystem`
2. Create directory at root level `./logs`
3. You install it and launch it as a subprocess with a config like "allowed directory = ./logs". You never write server code.
4. `uv add mcp`
5. Create mcp_client
6. Log file is working fine

## Checkpoint 8 — Evals

- Created `dataset.py` where expected test cases are written
- Created `scripts/evals` to call the analyze API
- Created `check_case()` and `run_evals()`
- Call and verify

## Checkpoint 9 — Finishing touch

1. Push the code — both GitHub and Bitbucket: https://bitbucket.org/jimmytrivedi/workspace/projects/JC
2. Review my code and then fix mistakes with Claude's help
3. Deploy the BE
4. Folder architecture

## Checkpoint 10 — LLM as judge

```
Case → analyze_with_claude(jd) → response
                                    ↓
                        judge_with_claude(jd, response) → {"verdict": "PASS", "reason": "..."}
```

So now we ask Claude again to analyze the response — that's the difference.

In Checkpoint 8, we were evaluating via our own expected I/O through Python code. Now in Checkpoint 10, we make a Claude API call to check it.

## Checkpoint 11 — API Auth

Right now `api.jimmytrivedi.in/analyze` is open to the world. Add API-key middleware (~20 lines). Anyone can hammer your Anthropic credits otherwise.

Added `Depends` on header as `API_KEY`.

## Checkpoint 12 — Prompt Caching

Implemented in claude_client:

```python
system=[
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}
    }
]
```

Prompt caching is working fine.

## Checkpoint 13 — Reranking

**Why:** Qdrant returns chunks by raw cosine similarity, which rewards surface similarity, not true relevance.

**Fix:** fetch a wider candidate pool, then let Voyage's reranker re-score and keep the best few.

Flow: we used to fetch `top_k=5` chunks, now we're fetching 20 chunks, then we use the Voyage `client.rerank` function which returns the top 5 chunks, and the flow continues.

## Checkpoint 14 — Second tool (search_web)

Give Claude an OPTIONAL `search_web(query)` tool. Unlike `search_resume` / `extract_requirements`
(always called), Claude calls this ONLY when a JD mentions unfamiliar tech it needs to look up
before judging fit. If everything in the JD is familiar, it skips the tool — and that choice
is the point: real agentic decision-making (when NOT to call), not a forced tool sequence.

Steps:

1. Create a new tool called `search_web()` with its schema
2. Here we're not using Anthropic's default `web_search` tool, instead we're going with a 3rd party called Tavily
3. Created a Tavily account, and installed `uv add tavily-python`
4. We gave a different prompt and the tool got called — it's working now.

## Checkpoint 15 — Structured outputs

**Why:** regex + `json.loads` could return wrong/incomplete data silently (a Python return hint and a prompt example don't enforce anything).

**Fix:** use native structured outputs so the API guarantees schema-valid JSON.

1. Switched `client.messages.create` → `client.messages.parse` with `output_format=Assessment`.
2. Dropped the regex/json parsing; return `response.parsed_output` (already validated).

## Checkpoint 16 — Streaming (SSE)

**Why:** the agent loop takes time; push progress instead of making the client wait for one big response.

SSE format: each event is `"data: {json}\n\n"` over one open connection.

1. Made `analyze_with_claude` a generator: yield a "tool" event per tool call, and a final "done" event with the result.
2. New endpoint `/analyze/stream` returns `StreamingResponse(generator, media_type="text/event-stream")`.

Note: `analyze_with_claude` is now a generator, so the old `/analyze` and `/log-application` are disabled.

## Checkpoint 17 — Agent instrumentation

Added a per-request trace (iterations, tools, tokens) + a total latency timer in `analyze_with_claude`.

Tokens accumulate with `+=` across loop iterations (dict resets each request).

Win it surfaced: trace showed 7 `search_resume` calls → ~101s. Capped searches to 2 in the system prompt → ~28s (~72% faster).

Root cause of remaining slowness: Voyage free tier = 3 RPM; each search does embed + rerank.

## Checkpoint 18 — Tool evaluation

Grade the agent's tool path, not just the final answer.

`eval_check_tools` consumes the generator, collects "tool" events, and asserts: `extract_requirements` is first, `search_resume` <= 2.

Reused the SSE yields as the trace source. Result: passed 3/3.

Note: hit Voyage 3 RPM during multi-case runs; raised `embed_query` backoff to 25s so it self-heals instead of crashing.

## Checkpoint 19 — RAG evaluation (relevance)

Grade retrieval directly, not the final answer.

`RAG_CASES` = list of (query, expected keyword). `rag_relevance_eval` calls `query_chunks` and asserts the keyword is in the returned chunks.

Bypasses Claude / the agent loop, so it tests retrieval alone. Result: passed 3/3.

## Checkpoint 20 — Observability (LangSmith)

Send traces to a dashboard instead of only terminal prints.

1. `uv add langsmith`; set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` in .env (project auto-creates on first trace).
2. Added `@traceable` on `analyze_with_claude` (decorate `run_tool` / `query_chunks` later for nested spans).

Result: each `/analyze` request shows up in the LangSmith dashboard with inputs, output, latency.

## Checkpoint 21 — Layered architecture

**Why:** `backend/` had grown into 13 flat files named after vendors (`voyage_client.py`, `qdrant_client_db.py`). `load_dotenv()` was called in 5 places, three files each built their own Anthropic client, `qdrant_client_db.py` and `rag.py` imported each other, and the SSE `"data: ...\n\n"` string was being built inside the agent loop. Nothing was testable without network + API keys.

**Fix:** split into layers with one-way imports. See the Architecture section at the top.

Steps:

1. `backend/config.py` — one `Settings` class. All env vars, model IDs, constants, and `PROJECT_ROOT`. `load_dotenv()` now runs exactly once in the whole repo.
2. Renamed vendor files by role and moved them to `adapters/` (`voyage_client` → `voyage_embedder`, `qdrant_client_db` → `qdrant_store`, etc.).
3. Broke the two-way import: `qdrant_store` now only holds the client; all orchestration moved to `services/retrieval.py`.
4. Moved the SSE framing out of the agent loop into `api/sse.py`. `analyze_with_claude` now yields plain dicts — which also made `eval_check_tools` simpler (no more string parsing).
5. Replaced `HTTPException` in the service layer with `domain/errors.py → AgentLoopExceeded`. FastAPI now exists only under `api/`.
6. Moved `chunk_by_char` out of the Voyage adapter — it's pure string logic, nothing to do with Voyage. Added `tests/` with the first real unit tests.
7. Swapped `print()` for `logging`, and consolidated the three Anthropic clients into `adapters/anthropic_llm.py`.

Verified end to end after the move: auth, both tools, Qdrant retrieval, prompt caching (3646 cached tokens), clean SSE frames.

Skipped on purpose: `Protocol` ports for the adapters. Only one implementation of each, so it would be indirection with no payoff.

## Checkpoint 22 — Agentic RAG

**Why:** Claude already fired multiple `search_resume` calls, but it decided the count up front from the JD — it never judged whether a result was actually good before searching again. That's blind multi-query, not reflection.

Done in two parts:

**1. Prompt-only reflection (lightest).** Added a step to the `SYSTEM_PROMPT` workflow: after a `search_resume` result, evaluate whether the chunks confirm/deny the requirement — refine and search again only if they were insufficient, otherwise move on. Turns "search twice because there are two topics" into "search again because the first result was weak."

**2. Explicit reflection in code.** The prompt hides the judgment inside Claude's reasoning; this makes it measurable.
- New `rate_chunks(query, chunks)` in `services/evaluation.py` — a separate Claude call (same shape as `judge_response`) that returns `{"sufficient": <bool>, "score": <float>}`, driven by `RATE_CHUNK_PROMPT` in `llm/prompts.py`.
- Wired into the agent loop in `analyzer.py`: after each `search_resume`, it calls `rate_chunks` and yields a `{"stage": "reflection", "sufficient": ...}` SSE event — emitted *after* the matching `tool` event so the stream reads tool → its reflection.

Verified live: the stream now shows a `reflection` event per search, and `sufficient` genuinely discriminates (a broad MVVM/CI-CD/testing search came back `false`, matching the gaps in the final assessment).

Stopped short on purpose: the reflection is **observed but not acted on** — the loop emits `sufficient` but doesn't yet branch on `false`. Making the loop react (force a refined re-search) is the natural next step.

## Checkpoint 23 — LangGraph

Rebuilt the hand-rolled agent loop as an explicit LangGraph state graph in `services/graph.py` (kept the old `analyze_with_claude` intact). Graph: `START → model → (tools_condition) → run_tools → model` cycle, ending `model → format → END`. `State(MessagesState)` adds an `assessment` field. Then ported the old loop's features one by one:

- **System prompt** — `call_model` prepends a `SystemMessage(SYSTEM_PROMPT)` each turn.
- **Structured output** — a `format` node calls `model.with_structured_output(Assessment)`; it appends a `HumanMessage` first, because Anthropic rejects assistant-prefill (the turn must end on a user message).
- **Reflection** — `search_resume_tool` self-rates its chunks via `rate_chunks` and logs the verdict (observed, not acted on — same as before).
- **SSE streaming** — `analyze_graph_stream` consumes `app.stream(stream_mode="updates")` and yields `{"stage": "tool"/"done"}` dicts; exposed at `POST /analyze/graph/stream` via `to_sse`.
- **Trace / instrumentation** — accumulates tool names + token counts from each `model` chunk's `usage_metadata`, logs elapsed time.
- **Prompt caching** — tagged the last system block **and** the last tool with `cache_control` (what `AnthropicPromptCachingMiddleware` does), verified correct on the wire.

**Caching finding:** it does not actually cache at this prompt size, and that's expected. Debugged it down to prefix size — the raw client caches fine with the *old* `tool_specs` (~1527-token prefix, `input_examples` make them fat) but not with the lean LangChain `@tool` versions (~1086-token prefix). The tags are correct and will activate automatically once the prefix grows; the old code cached almost incidentally because of its verbose tool definitions. Confirmed it's not a LangChain issue — the raw Anthropic client won't cache the lean prefix either.

Not ported (stays offline): `judge_response` LLM-as-judge lives in `scripts/evals.py`, not the live path.
---

## Checkpoint 24 — Agent orchestration / Multi-agent

Built a dynamic supervisor in `services/supervisor.py` (kept the single-agent graph intact).

- 3 specialist agents: `requirement_extractor` (parse JD), `matcher` (score fit vs resume), `bullet_writer` (tailored bullets) — each a focused LLM call, not a tool.
- Supervisor is an LLM that returns a `Route` (Literal of the 3 agents + FINISH); a conditional edge routes on `state["next"]`, each specialist loops back to the supervisor.
- Termination: agents append their name to a `completed` list in state (via `operator.add` reducer); the supervisor sees that list in its prompt and returns FINISH once all have run — no recursion guard or code short-circuit needed.
- Verified: runs each specialist once, then stops on its own (natural FINISH).

-------------------------------------------------------- PROJECT END ---------------------------------------------------