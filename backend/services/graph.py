from langchain_core import messages

from backend.services.retrieval import query_chunks
from backend.services.tool_runner import run_extract_requirements, run_search_web

from backend.adapters.anthropic_llm import model
from backend.llm.prompts import SYSTEM_PROMPT
from backend.domain.models import Assessment

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage

class State(MessagesState):
    assessment: Assessment

graph = StateGraph(State)

@tool()
def search_resume_tool(query: str):
    """Given the JD, fetch the relevant chunks that matches"""
    return query_chunks(query)

@tool()
def extract_requirements_tool(jd: str):
    """Extract requirements from this job description"""
    return run_extract_requirements(jd)

@tool()
def search_web_tool(query: str):
    """Use this tool if any keyword is unfamiliar"""
    return run_search_web(query)


tools = [search_resume_tool, extract_requirements_tool, search_web_tool]
model_with_tools = model.bind_tools(tools)

structured_model = model.with_structured_output(Assessment)

# Model node
def call_model(state: State):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
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


# This step will validate and create the blueprint internally
app = graph.compile()