import anthropic
from backend.domain.models import Assessment
from backend.domain.errors import AgentLoopExceeded
from backend.llm.prompts import SYSTEM_PROMPT
from backend.llm.tool_specs import search_resume, extract_requirements, search_web
from backend.services.tool_runner import run_tool
from backend.config import settings
from backend.adapters.anthropic_llm import client
import time
from anthropic.types import TextBlockParam, MessageParam
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

SYSTEM_BLOCKS: list[TextBlockParam]=[
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}
    }
]

def analyze(prompt: str) -> dict:
    result = None
    for event in analyze_with_claude(prompt):
        if event["stage"] == "done":
            result = event["result"]
    return result

@traceable()
def analyze_with_claude(prompt: str):
   messages: list[MessageParam] = [{"role": "user", "content": prompt}]
   start = time.perf_counter()
   trace = {"iteration": 0, "tools": [], "input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
   try:
       MAX_ITERATIONS = settings.max_iterations

       for iteration in range(MAX_ITERATIONS):
           trace["iteration"] = iteration
           response = client.messages.parse(
               model=settings.chat_model,
               max_tokens=1024,
               tools=[search_resume(), extract_requirements(), search_web()],
               output_format=Assessment,
               system=SYSTEM_BLOCKS ,
               messages=messages,
           )

           usage = response.usage
           trace["input_tokens"] += usage.input_tokens
           trace["output_tokens"] += usage.output_tokens
           trace["cache_read_input_tokens"] += usage.cache_read_input_tokens or 0

           # Response
           if response.stop_reason != "tool_use":
               break

           # Handle tool use
           tool_results = []

           for block in response.content:
               if block.type == "tool_use":
                   trace["tools"].append(block.name)
                   logger.info("Tool called: %s | input: %s", block.name, block.input)
                   result = run_tool(block.name, block.input) #Dispatcher
                   yield {"stage": "tool", "name": block.name}
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
           raise AgentLoopExceeded()
   except anthropic.BadRequestError as e:
       logger.exception("Claude API error")
       raise

   end = time.perf_counter()
   elapsed = end - start

   logger.info("Request completed in %.2fs", elapsed)
   logger.info("Trace: %s", trace)

   yield {"stage": "done", "result": response.parsed_output.model_dump()}
