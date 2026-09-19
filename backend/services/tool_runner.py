import json

from backend.config import settings

from backend.adapters.tavily_search import get_web_search_result
from backend.adapters.anthropic_llm import client

from backend.services.retrieval import query_chunks
from backend.llm.prompts import EXTRACT_REQUIREMENTS_PROMPT

from anthropic.types import MessageParam
from langsmith import traceable

def run_extract_requirements(jd: str) -> dict:
    prompt = EXTRACT_REQUIREMENTS_PROMPT.format(jd=jd)
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=settings.chat_model,
        max_tokens=512,
        messages=messages,
    )
    text = response.content[0].text
    return json.loads(text)

def run_search_web(query: str) -> dict:
    return get_web_search_result(query)

@traceable()
def run_tool(name, tool_input):
    if name == "search_resume":
        return query_chunks(tool_input["query"], tool_input.get("top_k", settings.top_k))
    if name == "extract_requirements":
        return json.dumps(run_extract_requirements(tool_input["jd"]))
    if name == "search_web":
        return run_search_web(tool_input["query"])

    return {"error": f"Unknown tool: {name}"}