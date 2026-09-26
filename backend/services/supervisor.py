import json
import operator
import time
import logging

from pydantic import BaseModel
from typing import Literal, Annotated

from backend.adapters.anthropic_llm import model
from backend.llm.prompts import SUPERVISOR_PROMPT, MATCHER_PROMPT, BULLET_WRITER_PROMPT

from backend.services.tool_runner import run_extract_requirements
from backend.services.retrieval import query_chunks

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage


logger = logging.getLogger(__name__)

AGENTS = ["requirement_extractor", "matcher", "bullet_writer"]

class State(MessagesState):
    next: str
    completed: Annotated[list[str], operator.add]   # append-only list of finished agents

class Route(BaseModel):
    next: Literal["requirement_extractor", "matcher", "bullet_writer", "FINISH"]

graph = StateGraph(State)

supervisor_model = model.with_structured_output(Route)


def supervisor(state: State):
    done = state.get("completed", [])
    context = (
        f"\n\nAgents already completed: {done or 'none'}."
        f" All agents that must run: {AGENTS}."
        f" Return FINISH once every agent has run."
    )
    messages = (
        [SystemMessage(content=SUPERVISOR_PROMPT + context)]
        + state["messages"]
        + [HumanMessage(content="Who should run next?")]
    )
    decision = supervisor_model.invoke(messages)
    return {"next": decision.next}

def requirement_extractor(state: State):
    jd = state["messages"][0].content
    requirements = run_extract_requirements(jd)
    return {
        "messages": [AIMessage(content=json.dumps(requirements))],
        "completed": ["requirement_extractor"],
    }

def matcher(state: State):
    requirement = state["messages"][0].content
    chunks = query_chunks(requirement)
    response = model.invoke([SystemMessage(content=MATCHER_PROMPT), HumanMessage(content=requirement + chunks)])
    return {"messages": [response], "completed": ["matcher"]}

def bullet_writer(state: State):
    jd = state["messages"][0].content
    chunks = query_chunks(jd)
    response = model.invoke([
        SystemMessage(content=BULLET_WRITER_PROMPT),
        HumanMessage(content=f"JD:\n{jd}\n\nResume chunks:\n{chunks}"),
    ])
    return {"messages": [response], "completed": ["bullet_writer"]}


# Nodes
graph.add_node("requirement_extractor", requirement_extractor)
graph.add_node("matcher", matcher)
graph.add_node("bullet_writer", bullet_writer)
graph.add_node("supervisor", supervisor)

# Edges
graph.add_edge(START, "supervisor")
graph.add_edge("requirement_extractor", "supervisor")
graph.add_edge("matcher", "supervisor")
graph.add_edge("bullet_writer", "supervisor")
graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],        # returns the supervisor's choice
    {
        "requirement_extractor": "requirement_extractor",
        "matcher": "matcher",
        "bullet_writer": "bullet_writer",
        "FINISH": END,
    },
)

def analyze_supervisor_stream(query: str):
    trace = {"tools": [], "input_tokens": 0, "output_tokens": 0, "cache_read": 0}
    start = time.perf_counter()
    inp = {'messages': [{'role': 'user', 'content': query}]}
    result = None

    for chunk in app.stream(
        input=inp,
        stream_mode="updates"
    ):
        for node, update in chunk.items():
            if node in ("requirement_extractor", "matcher", "bullet_writer"):
                yield {"stage": "agent", "name":node}
                result = update["messages"][-1].content
    yield {"stage": "done", "result": result}

    end = time.perf_counter()
    elapsed = end - start

    logger.info(f"elapsed {elapsed}")
    logger.info(f"Trace: {trace}")

app = graph.compile()
