import logging
import time

from backend.services.retrieval import query_chunks
from backend.services.tool_runner import run_extract_requirements, run_search_web
from backend.services.evaluation import rate_chunks

from backend.adapters.anthropic_llm import model
from backend.llm.prompts import SYSTEM_PROMPT
from backend.domain.models import Assessment

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

class State(MessagesState):
    assessment: Assessment

logger = logging.getLogger(__name__)
graph = StateGraph(State)

@tool()
def search_resume_tool(query: str):
    """Given the JD, fetch the relevant chunks that matches"""
    chunks = query_chunks(query)
    chunks_result = rate_chunks(query, chunks)
    logger.info("stage: %s | sufficient: %s", "reflection", chunks_result)
    return chunks

@tool()
def extract_requirements_tool(jd: str):
    """Extract requirements from this job description"""
    return run_extract_requirements(jd)

@tool()
def search_web_tool(query: str):
    """Use this tool if any keyword is unfamiliar"""
    return run_search_web(query)


tools = [search_resume_tool, extract_requirements_tool, search_web_tool]

# Bind tools, then tag the LAST tool dict with cache_control so the whole
# tools + system prefix becomes one cacheable block (what the middleware does).
model_with_tools = model.bind_tools(tools)
model_with_tools.kwargs["tools"][-1]["cache_control"] = {"type": "ephemeral"}

structured_model = model.with_structured_output(Assessment)

# Model node
def call_model(state: State):
    SYSTEM_BLOCKS = SystemMessage(content=[
        {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
    ])

    messages = [SYSTEM_BLOCKS] + state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}  #state update

# Format response
def format_response(state: State):
    messages = state["messages"] + [HumanMessage(content="Now return the final structured assessment.")]
    result = structured_model.invoke(messages)
    return {"assessment": result}

# Tools node
tool_node = ToolNode(tools)

# Wiring Nodes with graph
graph.add_node("model", call_model)
graph.add_node("run_tools", tool_node)
graph.add_node("format", format_response)

# Wiring Edges with graph
graph.add_edge(START, "model")
graph.add_edge("run_tools", "model")
graph.add_edge("format", END)
graph.add_conditional_edges("model", tools_condition, {"tools": "run_tools", END: "format"})

def analyze_graph_stream(query: str):
    trace = {"tools": [], "input_tokens": 0, "output_tokens": 0, "cache_read": 0}
    start = time.perf_counter()
    inp = {'messages': [{'role': 'user', 'content': query}]}
    for chunk in app.stream(
        input=inp,
        stream_mode="updates",
    ):
        if "model" in chunk:
            msg = chunk["model"]["messages"][-1]
            meta = msg.usage_metadata
            print("META:", meta)

            trace["input_tokens"] += meta["input_tokens"]
            trace["output_tokens"] += meta["output_tokens"]
            trace["cache_read"] += meta["input_token_details"]["cache_read"]

        if "run_tools" in chunk:
            for msg in chunk["run_tools"]["messages"]:
                trace["tools"].append(msg.name)
                yield {"stage": "tool", "name": msg.name}
        if "format" in chunk:
            yield {"stage": "done", "result": chunk["format"]["assessment"].model_dump()}

    end = time.perf_counter()
    elapsed = end - start

    logger.info(f"elapsed: {elapsed}")
    logger.info(f"Trace: {trace}")
# This step will validate and create the blueprint internally
app = graph.compile()