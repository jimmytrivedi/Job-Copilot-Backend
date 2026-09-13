from fastapi import HTTPException

import anthropic
import os
import json
from backend.models import Assessment
from backend.prompts import SYSTEM_PROMPT
from backend.qdrant_client_db import query_chunks
from backend.tools import search_resume, extract_requirements, run_extract_requirements, search_web, run_search_web
from dotenv import load_dotenv
import time

# Test git

load_dotenv() # Reads the .env file and loads its variable into os.environ
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_with_claude(prompt: str) -> Assessment:
   messages = [{"role": "user", "content": prompt}]
   start = time.perf_counter()
   trace = {"iteration": 0, "tools": [], "input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
   try:
       MAX_ITERATIONS = 6

       for iteration in range(MAX_ITERATIONS):
           trace["iteration"] = iteration
           response = client.messages.parse(
               model="claude-sonnet-4-6",  # List of Model ID: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions
               max_tokens=1024,
               tools=[search_resume(), extract_requirements(), search_web()],
               output_format=Assessment,
               system=[
                   {
                       "type": "text",
                       "text": SYSTEM_PROMPT,
                       "cache_control": {"type": "ephemeral"}
                   }
               ],
               messages=messages,
           )

           usage = response.usage
           trace["input_tokens"] += usage.input_tokens
           trace["output_tokens"] += usage.output_tokens
           trace["cache_read_input_tokens"] += usage.cache_read_input_tokens

           # Response
           if response.stop_reason != "tool_use":
               break

           # Handle tool use
           tool_results = []

           for block in response.content:
               if block.type == "tool_use":
                   trace["tools"].append(block.name)
                   print(f"Tool called: {block.name} | input: {block.input}\n")
                   result = run_tool(block.name, block.input) #Dispatcher
                   yield f'data:{{"stage": "tool", "name": "{block.name}"}}\n\n'
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

   end = time.perf_counter()
   elpsed = end - start
   print(f"Request time is {elpsed} seconds")
   print(f"trace {trace}")

   yield f'data:{{"stage": "done", "result": {response.parsed_output.model_dump_json()}}}\n\n'


def run_tool(name, tool_input):
    if name == "search_resume":
        return query_chunks(tool_input["query"], tool_input.get("top_k", 5))
    if name == "extract_requirements":
        return json.dumps(run_extract_requirements(tool_input["jd"]))
    if name == "search_web":
        return run_search_web(tool_input["query"])

    return {"error": f"Unknown tool: {name}"}
