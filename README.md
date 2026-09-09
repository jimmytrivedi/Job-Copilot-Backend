# Checkpoint 0 — Environment ready
- Created project
- Created .env file and added API keys (Anthropic, Voyage AI, Qdrant Key, Qdrant URL)
[Voyage AI creates embedding models that convert text into vector]
[Qdrant is Vector Database, it is require to store embedding created by Voyage AI]
[Qdrant URL and key to access DB]

- Added .env file in .gitignore
- Install / Verify Node.js [node --version]
- Create root level folder to put resume - corpus/resume.md
- Need to install packages: Local env

- Local env setup command
uv init
uv venv
source .venv/bin/activate
uv add fastapi "uvicorn[standard]"

- Delete src folder, so that we can run / root everything from main.py
- Add files in Git
- gitignore: uv.lock, .env

Go to pyproject.toml and delete from bottom 2 block, because this we'll run from main.py
[project.scripts]
jobsearch = "jobsearch:main"

[build-system]
requires = ["uv_build>=0.12.5,<0.13.0"]
build-backend = "uv_build"



# Checkpoint 1 — FastAPI skeleton alive
Update main.py, so that you can run server

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

Command: uvicorn main:app --reload
Output: Server is running



# Checkpoint 2 — Claude responds to a real request
- Create post request /analye
- create backend/models.py
- create class

from pydantic import BaseModel

class Assessment(BaseModel):
    jd: str
    resume: str

Write a post function with return type of: @app.post("/analyze")

Create claude_client to make use of claude API
uv add anthropic (To get Anthropic packages)
uv add python-dotenv (To directly read API keys from .env file)

-------------------------------
import anthropic
import os

from dotenv import load_dotenv

load_dotenv() # Reads the .env file and loads its variable into os.environ
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-6",      #List of Model ID: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
-------------------------------

After writing basic claude client setup, print it and run below command
uv run claude_client.py 
Working fine, got response from claude: Hello! How are you doing? Is there something I can help you with today? 😊
Now, next task is use claude API to assess the JD with resume, means inside main.py we should call claude_client fun

@app.post("/analyze")
def analyze(assessment: Assessment) -> Assessment:
    result = analyze_with_claude(f"JD: {assessment.jd}\nResume: {assessment.resume}")
    return {"result": result}

Got status code 200 with unformatted response. But it is analyzing. Need structure / schema improvement
To improve accuracy, now add system prompt, so create prompts.py
system=SYSTEM_PROMPT



# Checkpoint 3 — Structured output
To provide input and output format with JSON
1. Update Assessment class - rename AnalyzeRequest: this is for input
2. Create new class inside models.py - Assessment - this is for output
    match_score: int
    strengths: list[str]
    gaps: list[str]
    verdict: str
3. Update system prompt and define Assessment class fields
4. Need to Add JSON parser

We're getting response based on JSON



# Checkpoint 4 — RAG
Goal: Instead of sending resume as a prompt, use it from corpus/resume.md, it means this need to upload on Qdrant DB (Vector DB) using Voyage AI
- Command: uv add voyageai
- Create voyage_client

client = voyageai.Client(api_key=os.environ.get("VOYAGE_API_KEY"))
result = client.embed(texts = ["Hello World"], model="voyage-4-large")
print(result)

Able to convert from text to embeddings
uv run voyage_client.py 
<voyageai.object.embeddings.EmbeddingsObject object at 0x109abef90>

Now need to store into Qdrant DB
uv add qdrant-client
- Create qdrant_client_db.py
- Create client object, new collection and store it using client.upsert
- Once this succeed, add long text, break into chunk and store inside Qdrant, chunk wise: get_embeddings_by_chunks()

Next:
Need to store resume instead of manual dummy text
Reading corpus/resume.md

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "corpus/resume.md"), "r") as f:
        text = f.read()
and passing text: chunk_by_char(text)

Question: Am I pasting entire resume with every request? 
Answer: Need code correction first
1. Inside rag.py - create new function insert_vectors, and what we were doing insertion logic inside qdrant_client, that move in insert_vectors()
2. Need to write retrival function, which will retrieve data from Qdrant Top-K chunk and append in claude query 
3. Create rag.py and write retrieve func with query params 
4. To retrieve data based on query params, we should convert query to embeddings and then pass to Qdrant 
5. Receive request (jd only) → retrieve chunks from Qdrant → build prompt with jd + chunks → call Claude → return

Output: Resume is now not attached in every request.



# Checkpoint 5 — Tool calling
Why we need Tool calling: In our current app, we manually do retrieval — we always call Qdrant before calling Claude, regardless of whether it's needed.
With tool calling, you'd instead give Claude a search_resume(query) tool, and Claude itself decides when to call it, what query to search for, 
and even whether to search multiple times. The control shifts from your code to the model, making the system more flexible and agent-like.

- Create Tool - tools.py - search_resume()
- Create schemas.py to provide inside tools. Tools need schemas
- Provide Tool access to Claude
- Claude is calling tool. Now need to handle Claude response: ToolUseBlock
- Claude is using tool and we're getting 200.



# Checkpoint 6 — Agent loop
Tailored bulllets support - Means Rewrite resume bullet points based on JD
Rule: Tailored bulllets must only mention skills that appear in candidate's resume content.
Add more tools
Agent loop safety guard - MAX_ITERATIONS = 5
Updated prompt and many more correction



# Checkpoint 7 — MCP
The Claude JD analysis, we're going to write in one file.
We're writing this file through MCP instead of normal file functionality.
Our logic should write / touch the file only in allowed directory, otherplace it shpuld throw error.
Python code is client and File system is server in this case

1. Install MCP server as a filesystem by this command: npm install -g @modelcontextprotocol/server-filesystem
2. Create director at root level ./logs
2. You install it and launch it as a subprocess with a config like "allowed directory = ./logs". You never write server code.
3. uv add mcp
4. Create mcp_client
5. Log file is working fine



# Checkpoint 8 — Evals
Created Dataset.py where expected test case written
Created scripts/evals to call analyze api
Created check_case() and run_evals()
Call and verify




# PENDING
1. Push the code - Both Github and Bitbucket: https://bitbucket.org/jimmytrivedi/workspace/projects/JC
2. Review my code and then mistakes will fix with claude help
- Deploy the BE
- streaming
- Folder architecture
- Swap MCP with Google Drive MCP
- Add LLM-as-judge to your eval suite 
- Add a new tool that Claude actually decides whether to call (not just how)
- Write the portfolio README from scratch

- Update below:
1. In Linkedin project section - Add this project and provide GitHub link (from github/com/jimmytrivedi/JobSearch)
2. In resume Add this line: Basic Understanding of LLM. Also Created basic AI - Job Search project with use of prompt engineering, RAG, MCP, 
3. Add similar AI related things in LinkedIn About section as well.

- Solve one question in Python language on Leetcode






