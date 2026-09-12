from fastapi import HTTPException

import anthropic
import os
import json, re

from backend.models import Assessment, AnalyzeRequest
from backend.prompts import SYSTEM_PROMPT
from backend.qdrant_client_db import query_chunks
from backend.tools import search_resume, extract_requirements, run_extract_requirements, search_web, run_search_web
from dotenv import load_dotenv

# Test git

load_dotenv() # Reads the .env file and loads its variable into os.environ
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_with_claude(prompt: str) -> Assessment:
   messages = [{"role": "user", "content": prompt}]
   try:
       MAX_ITERATIONS = 6
       for iteration in range(MAX_ITERATIONS):
           response = client.messages.create(
               model="claude-sonnet-4-6",  # List of Model ID: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
               max_tokens=1024,
               tools=[search_resume(), extract_requirements(), search_web()],
               system=[
                   {
                       "type": "text",
                       "text": SYSTEM_PROMPT,
                       "cache_control": {"type": "ephemeral"}
                   }
               ],
               messages=messages,
           )

           # Response
           if response.stop_reason != "tool_use":
               break

           # Handle tool use
           tool_results = []
           for block in response.content:
               if block.type == "tool_use":
                   print(f"Tool called: {block.name} | input: {block.input}\n")
                   result = run_tool(block.name, block.input) #Dispatcher
                   tool_results.append(
                       {
                           "type": "tool_result",
                           "tool_use_id": block.id,
                           "content": result
                       }
                   )

           messages.append({"role": "assistant", "content": response.content})
           messages.append({"role": "user", "content": tool_results})
       else:
           raise HTTPException(
               status_code=504,
               detail=f"Agent loop exceeded {MAX_ITERATIONS} iterations"
           )
   except anthropic.BadRequestError as e:
       print(f"Claude API error: {e}")
       raise


   try:
       text = next(b.text for b in response.content if b.type == "text")
       match = re.search(r"\{.*\}", text, re.DOTALL)
       clean = match.group(0) if match else text.strip()
       return json.loads(clean, strict=False)
   except json.JSONDecodeError as e:
       print(f"Failed to pass Claude response: {e}")
       print(f"Raw text: {text}")
       raise HTTPException(status_code=502, detail="Claude returned invalid JSON")
   except Exception as e:
       print(f"Unexpected error: {e}")
       raise

def run_tool(name, tool_input):
    if name == "search_resume":
        return query_chunks(tool_input["query"], tool_input.get("top_k", 5))
    if name == "extract_requirements":
        return json.dumps(run_extract_requirements(tool_input["jd"]))
    if name == "search_web":
        return run_search_web(tool_input["query"])

    return {"error": f"Unknown tool: {name}"}
