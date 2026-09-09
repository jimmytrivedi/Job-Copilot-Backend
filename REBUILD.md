# Job Copilot — self-directed rebuild

You built this project once with a guide. Now build it again without one.

**Rules:**
- Do NOT open the reference implementation.
- Do NOT ask a chat assistant "how do I do X."
- Google, read docs, read errors, think.
- At each checkpoint below, run the verification. If the output doesn't match, you've drifted — debug (yourself) before moving on.
- Time yourself. First rebuild might take 12 hours. Third rebuild might take 3. That's the point.

**Goal:** you finish able to explain every decision and rewrite each file cold.

---

## Setup checklist

Before starting:
- [ ] A new empty folder outside your existing project
- [ ] API keys for Anthropic, Voyage AI, Qdrant Cloud
- [ ] Node.js installed
- [ ] A password manager entry with all four keys backed up
- [ ] Your resume (2 pages, plain text) ready to paste

**Do NOT copy anything from your old project — not files, not commands, not `.env`. Retype from memory.**

---

## Checkpoint 0 — Environment ready

**Goal:** Python project scaffolded, packages installed, secrets loading through a typed config.

**Verify:**
- Running a one-line Python script that imports your config object prints a non-empty prefix of your Anthropic API key.
- If any of the four env vars is missing or misnamed, the import FAILS LOUDLY.
- Your `.env` is git-ignored.

**Self-check questions:**
- Which Python version did you pin, and why?
- Why load secrets through a typed config object instead of `os.getenv` scattered through the code?
- What happens if a required env var is missing at server startup vs mid-request? Which is better and why?

**If you skip this and move on:** later steps will fail with confusing NoneType errors instead of a clear "missing key" message. That's your signal you skipped the guard rail.

---

## Checkpoint 1 — FastAPI skeleton alive

**Goal:** A server that runs, auto-reloads on code changes, and exposes an auto-generated API documentation page.

**Verify:**
- Server starts with one command.
- Opening the API docs page in your browser lists at least one endpoint.
- Hitting a `/health` endpoint returns a valid JSON response indicating the service is up.

**Self-check questions:**
- What does the framework do for you that a bare HTTP library wouldn't?
- Why is `/health` a universal first endpoint?
- Where does the auto-generated docs page get its schema from?

**If you skip:** you'll be testing later endpoints via `curl` or Postman when you could be one-clicking them. Also, your typed request/response models won't give you as much value.

---

## Checkpoint 2 — Claude responds to a real request

**Goal:** An endpoint that accepts a JD + resume as JSON and returns Claude's honest, blunt assessment as prose.

**Verify:**
- POST a JD + resume via the auto docs page → get back non-empty text.
- POST a deliberate mismatch (Android dev applying to ML role) → the returned text calls out gaps directly. It does NOT hedge or claim "some transferable skills." If it does, your system prompt isn't blunt enough.
- Iterating on the prompt actually changes the tone. Prove it — run the same mismatch with a normal prompt vs your "blunt hiring manager" prompt and read both outputs.

**Self-check questions:**
- What is the role of the `system` parameter vs the `messages` parameter?
- Why does a Claude call *require* `max_tokens`?
- Where should the prompt live in your project layout, and why?

**If you skip:** you'll build a copilot that lies politely. The mismatch test is your honesty gate.

---

## Checkpoint 3 — Structured output

**Goal:** Same endpoint, but the response is a validated JSON object with a `match_score`, `strengths`, `gaps`, and `verdict`.

**Verify:**
- Response is a clean JSON object matching your defined shape — no markdown, no prose wrapping the JSON.
- If Claude returns malformed JSON (missing field, wrong type), your server responds with a clear error, not a silent success.
- The mismatch test now gives you a `match_score` under 25.
- The strong-fit test gives you a `match_score` between 50 and 80.

**Self-check questions:**
- Why demand JSON output from the LLM instead of parsing prose?
- What are three common failure modes when an LLM produces JSON, and how do you handle each?
- Why validate the JSON on the way OUT (into your model) instead of trusting the LLM?

**If you skip:** downstream steps (RAG results feeding into gaps, evals scoring gaps, Android rendering) all fall apart because you have prose where you need structure.

---

## Checkpoint 4 — RAG

**Goal:** Instead of sending your whole resume with every request, the server retrieves only the most relevant chunks from a vector database.

**Verify:**
- Ingest script populates the vector DB — exit code 0, no errors.
- Query with an Android-focused JD → retrieved chunks are Android-related.
- Query with a Python-backend JD → retrieved chunks are different (and closer to whatever backend/API content exists in your corpus).
- If the top result for both JDs is the same chunk, RAG is broken.
- `/analyze` request now sends ONLY the JD (not the resume) and the response quality is at least as good as before.

**Self-check questions:**
- Why is chunk size the biggest lever for RAG quality? What happens if it's too small? Too large?
- What is the difference between `input_type="document"` and `input_type="query"`? What breaks if you use the wrong one?
- Why do we use *cosine* distance for text embeddings and not, say, Euclidean?
- Why is ingest a separate script, not part of the server startup?

**If you skip:** you'll paste your whole resume into every prompt forever. Works for a 2-page resume; doesn't scale.

---

## Checkpoint 5 — Tool calling

**Goal:** Instead of Claude free-forming the assessment, it FIRST calls a tool to extract structured JD requirements, then produces the assessment.

**Verify:**
- Passing a JD makes Claude call your tool.
- Tool output is structured (must-have list, nice-to-have list, years).
- Assessment gaps are now more *surgical* — each gap corresponds to a specific extracted requirement.

**Self-check questions:**
- What is the difference between advertising a tool and forcing Claude to call it? Name the two API mechanisms.
- When Claude calls a tool, its response has a stop reason of what? What field on the response block carries the tool call's arguments?
- How does the ID field pair a tool call with its result? What happens if you get it wrong?
- Why can a tool executor itself be another LLM call?

**If you skip:** you can build the rest, but the assessment will feel vibey rather than checked-against-requirements. Evals in Checkpoint 8 will be less useful.

---

## Checkpoint 6 — Agent loop

**Goal:** One `/analyze` call now runs multiple reasoning steps: extract requirements → assess → tailor resume bullets → return everything.

**Verify:**
- Response now includes a `tailored_bullets` array.
- Bullets are grounded in your retrieved experience — every skill mentioned appears in your resume.
- The loop has a max iteration guard. If Claude misbehaves, the request doesn't hang forever.
- Latency is noticeably higher than Checkpoint 5. That's expected — multiple tool calls.

**Self-check questions:**
- What decides the sequence of tool calls — your Python code, or the LLM?
- What is the stopping condition of your loop, and where is it enforced (Python side vs prompt side)?
- Why is `MAX_ITERATIONS` a non-negotiable safety guard?
- What is "assistant prefill" and when would you use it here?

**If you skip:** you have a diagnostic tool (score, gaps). Skipping the agent means you don't have an *action-taking* tool. Big difference for portfolio and utility.

---

## Checkpoint 7 — MCP

**Goal:** A `/log-application` endpoint that writes a record of each analyzed JD to persistent storage via the Model Context Protocol, using a filesystem MCP server.

**Verify:**
- Hitting `/log-application` returns the name of a new file.
- That file exists on disk in your designated logs folder.
- Trying to write outside the allowed directory is refused by the MCP server (verify by attempting a malicious path).
- Your logs folder is git-ignored.

**Self-check questions:**
- What is MCP a standard for, in one sentence?
- What are the two sides of MCP (client and server), and which one is your code?
- Why does the server require you to declare an allowed directory upfront?
- How would you swap this filesystem backend for a Google Drive backend? What lines of code change?

**If you skip:** you have an analyzer, not a copilot. Persistent history is what turns "answering questions" into "helping across sessions."

---

## Checkpoint 8 — Evals

**Goal:** A script that runs your dataset of JD/expected-gap pairs through the pipeline and prints a pass rate.

**Verify:**
- Dataset has at least 3 diverse cases (a fit, a mismatch, an edge case).
- Runner prints per-case results and an aggregate `passed: N/M`.
- Runner catches: coverage (are real gaps surfaced), hallucination (do tailored bullets mention gap terms), score sanity (is the score in the expected range).
- Deliberately break something (weaken the system prompt, remove a check) → pass rate drops. Undo → pass rate recovers.
- You produce a **before/after** measurement — the pass rate BEFORE some fix, then AFTER. This is the portfolio number.

**Self-check questions:**
- Why can't you use `assertEquals` on LLM output?
- What is "LLM-as-judge" and when would you upgrade to it instead of substring matching?
- Why measure across MULTIPLE runs of the same case? What does that reveal that a single run doesn't?
- Why is YOU being the ground truth what makes this eval meaningful?

**If you skip:** you have a demo. Not a measured product. In a portfolio, that's the difference between an interview and a rejection.

---

## Checkpoint 9 — Android client

**Goal:** A single-screen Compose app that talks to your backend.

**Verify:**
- Pastes a JD, hits Analyze, sees score + strengths + gaps + bullets rendered.
- "Log this application" button writes to the backend's log folder.
- Errors show as snackbars, never crash the app.
- Rotate the device mid-view — assessment survives.
- Long JDs (thousands of characters) analyze successfully.

**Self-check questions:**
- Why is `10.0.2.2` the emulator's alias for the host, and what would you use on a physical device?
- What OkHttp default breaks a 25-second `/analyze` call, and how do you fix it?
- Why does Android need explicit permission for cleartext HTTP to localhost?
- Why does the ViewModel own the state and the Composable just render?

**If you skip:** no demo video. And no demo video = no interview signal for anything that isn't a backend role.

---

## Golden path checkpoints — non-negotiable

If you drift, one of these usually fails first. Watch for them:

- **Env vars fail at startup**, not mid-request → Checkpoint 0 done right
- **A mismatch JD scores under 25** → your prompt is honest
- **JSON output is parseable in one shot** → your prompt+model contract holds
- **Retrieval differs for different JDs** → your embeddings are meaningful
- **Claude USES your tool, not just describes it** → you passed the schema correctly
- **`tailored_bullets` never mentions a gap term** → the guardrail works
- **The MCP write refuses paths outside the sandbox** → capability boundary works
- **Eval pass rate moves when you change one thing** → your evals actually measure

Any of these silently going the wrong way = you have a bug you're not seeing yet.

---

## When you get stuck

In order of what to try:

1. **Read the error carefully.** Bottom of the traceback is the error; the middle is context. Which file, which line, what type of error?
2. **Print the raw output of the API call that failed.** Nine times out of ten the LLM produced something you didn't expect, and printing it tells you exactly.
3. **Google the error message.** Include the library name.
4. **Read the SDK's official docs.** Not blog posts — the SDK docs.
5. **Rubber-duck out loud.** Describe the flow to an imaginary listener. You'll catch it halfway through.
6. **Take a break.** Stuck for over an hour? Come back tomorrow. Really.

**Only after all six**, and only if you're truly blocked, ask a chat assistant a specific narrow question — not "how do I do X" but "why does Y specific error say Z?"

---

## Rebuild success criteria

You've internalized the project when:

- [ ] You rebuild the whole backend in under 6 hours without opening the old repo.
- [ ] You can describe every file's job in one sentence.
- [ ] You can draw the architecture diagram from memory.
- [ ] You can explain each of the self-check questions above without lookup.
- [ ] You've changed something the original didn't have — a new tool, a different embedding provider, a new eval case — and it works.

The last bullet is the actual signal. Everything before that is memorization. The last one is design.

---

## After the rebuild

If you finished at least twice without help, you're ready for anything else in this stack. Next moves:

- Deploy your backend somewhere (Railway/Render/Fly free tier)
- Swap the filesystem MCP for Google Drive MCP
- Add LLM-as-judge to your eval suite
- Add a new tool that Claude actually decides *whether* to call (not just how)
- Write the portfolio README from scratch

Good luck. This is the part where you become a builder.
