---
name: add-tool
description: Add a new Claude tool to the agent loop, or modify an existing one. Use when the user wants the agent to gain a new capability, asks to "add a tool", or when a tool needs a new input field. Covers the schema, declaration, executor, dispatcher, and system prompt — miss one and the tool silently never fires.
---

# Adding a Claude tool

A tool touches **five** places. Skipping any one produces a silent failure, not an error.

## 1. JSON schema — `backend/llm/tool_specs.py`

```python
MY_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "What this field is for"}
    },
    "required": ["query"]
}
```

Every property needs a `description` — Claude reads it to decide how to fill the field.

## 2. Declaration — same file

```python
def my_tool():
    return {
        "name": "my_tool",
        "description": "When to call this. Be explicit about WHEN, not just what.",
        "input_schema": MY_TOOL_SCHEMA,
        "input_examples": [
            {"query": "a realistic call"},
            {"query": "a second, differently-shaped call"}
        ]
    }
```

The `name` here must match the dispatcher string in step 4 exactly.

## 3. Executor — `backend/services/tool_runner.py`

```python
def run_my_tool(query: str) -> str:
    return some_adapter_function(query)
```

Rules:
- If it calls an external service, the HTTP/SDK call goes in `backend/adapters/`, not here
- Return a `str` or JSON-serializable value — `run_tool`'s output goes straight into a `tool_result` block
- Dict returns must be `json.dumps`'d (see `run_extract_requirements`)

## 4. Dispatcher — `run_tool` in the same file

```python
    if name == "my_tool":
        return run_my_tool(tool_input["query"])
```

Use `tool_input.get("x", default)` for any field not in `required`.

## 5. Register — `backend/services/analyzer.py`

Add to the import and the `tools=[...]` list:

```python
from backend.llm.tool_specs import search_resume, extract_requirements, search_web, my_tool
...
tools=[search_resume(), extract_requirements(), search_web(), my_tool()],
```

## 6. System prompt — `backend/llm/prompts.py`

`SYSTEM_PROMPT` contains a numbered **Workflow** section. If the new tool has ordering or call-count constraints, state them there. Claude follows that workflow far more reliably than tool descriptions alone.

## Verify

```bash
uv run python -c "import main; print('OK')"
```

Then run one live request and confirm the tool appears in the trace:

```bash
uv run python -c "
from fastapi.testclient import TestClient
from backend.config import settings
import main
c = TestClient(main.app)
r = c.post('/analyze/stream', json={'jd':'<a JD that should trigger it>'},
           headers={'X-API-KEY': settings.api_key})
print(r.text)
"
```

The stream emits `{"stage": "tool", "name": "my_tool"}` when it fires. If it never appears, the tool description or the system prompt workflow is the problem — not the code.

## Common silent failures

| Symptom | Cause |
|---|---|
| Tool never called | Vague `description`, or not mentioned in `SYSTEM_PROMPT` workflow |
| `{"error": "Unknown tool: ..."}` | Step 4 missing, or name mismatch with step 2 |
| `KeyError` in the executor | Reading a field that isn't in `required` without `.get()` |
| Agent loops to `AgentLoopExceeded` | Tool returns something Claude can't act on; check it returns text, not a raw object |
