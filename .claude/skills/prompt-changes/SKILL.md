---
name: prompt-changes
description: Edit prompts in backend/llm/prompts.py safely. Use when changing SYSTEM_PROMPT, JUDGE_PROMPT, or EXTRACT_REQUIREMENTS_PROMPT, adding a placeholder, or when a prompt change produces a KeyError, malformed JSON, or a cache-hit drop.
---

# Editing prompts

All prompt text lives in `backend/llm/prompts.py`. Nowhere else — no inline f-strings in services.

## Brace escaping

Prompts are rendered with `str.format()`, so **every literal brace must be doubled**.

| You want Claude to see | You write |
|---|---|
| `{` | `{{` |
| `}` | `}}` |
| value substituted | `{jd}` |

This bites hardest on JSON shape examples:

```python
EXTRACT_REQUIREMENTS_PROMPT = """Respond with raw JSON only.

Shape:
{{
  "must_have": [<string>, ...]
}}

JD:
{jd}
"""
```

A single unescaped `{` gives `KeyError: '\n  "must_have"'` at call time, not import time — so it survives `import main`.

### Verify escaping before committing

```bash
uv run python -c "
from backend.llm.prompts import EXTRACT_REQUIREMENTS_PROMPT as P
print(P.format(jd='TEST'))"
```

Output should show single braces and `TEST` in place.

Current placeholders:

| Prompt | Placeholders | Used by |
|---|---|---|
| `SYSTEM_PROMPT` | none — never `.format()`ed | `services/analyzer.py` |
| `EXTRACT_REQUIREMENTS_PROMPT` | `{jd}` | `services/tool_runner.py` |
| `JUDGE_PROMPT` | `{jd}`, `{response}` | `services/evaluation.py` |

`SYSTEM_PROMPT` contains literal single braces in its example block. It is safe **only because nothing calls `.format()` on it.** If you ever add a placeholder to it, you must double every existing brace in that file at the same time.

## Prompt caching

`SYSTEM_PROMPT` is sent inside `SYSTEM_BLOCKS` in `services/analyzer.py` with:

```python
"cache_control": {"type": "ephemeral"}
```

Rules:
- Keep `cache_control` on the **last** block of the cached prefix
- Any edit to `SYSTEM_PROMPT` invalidates the cache — the next request rebuilds it
- Confirm caching still works: run one request and check the logged trace for a non-zero `cache_read_input_tokens`. It should be in the thousands. If it's 0 on a repeat request, the prefix is no longer stable.

## Structured output

`analyzer.py` uses `client.messages.parse(output_format=Assessment)`. The JSON contract is enforced by the `Assessment` model in `backend/domain/models.py`, not by prompt text.

So if you change the output shape, edit **both**:
1. `Assessment` in `domain/models.py`
2. The example JSON at the bottom of `SYSTEM_PROMPT`

Changing only the prompt does nothing; changing only the model produces a mismatch Claude wasn't told about.

## The Workflow section

`SYSTEM_PROMPT` has a numbered workflow that constrains tool use ("call extract_requirements first", "search_resume AT MOST 2 times"). `eval_check_tools` in `scripts/evals.py` asserts exactly those constraints.

Change the workflow → update the assertions in `eval_check_tools` → re-run:

```bash
uv run python -m scripts.evals
```

## Checklist after any prompt edit

1. `.format()` smoke test above (if the prompt has placeholders)
2. `uv run python -c "import main; print('OK')"`
3. One live request; check `cache_read_input_tokens > 0` in the trace log
4. Re-run the eval mode matching what you changed (see `run-and-eval` skill)
