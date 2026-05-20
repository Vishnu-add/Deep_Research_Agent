from typing import TypedDict, Literal, List, Dict, Any

from langgraph.graph import StateGraph, START, END

from src.backend.common_utils import *

MAX_LOOPS = 3


class State(TypedDict):

    query: str

    subqueries: List[str]

    sources: List[Any]

    validated_sources: List[Any]

    reflection: Dict[str, Any]

    plan: str

    final_answer: str

    loop_count: int

    satisfied: bool


def search_node(state: State):

    query = state["query"]

    results = search_tool.run(query)

    state["sources"].append(results)

    state["validated_sources"].append(results)

    return state


def reflection_node(state: State):

    response = invoke_llm(
        "You are a reflection agent.",
        f"""
        Analyze whether the retrieved information is sufficient.

        Query:
        {state['query']}

        Sources:
        {state['sources']}

        Return STRICT JSON:
        {{
            "satisfied": true,
            "reason": "..."
        }}
        """
    )

    parsed = extract_json(response)

    if parsed is None:

        parsed = {
            "satisfied": False,
            "reason": "Parsing failed"
        }

    state["reflection"] = parsed

    state["satisfied"] = parsed["satisfied"]

    state["loop_count"] += 1

    return state


def synthesis_node(state: State):

    response = invoke_llm(
        "You are a synthesis agent.",
        f"""
        Generate a detailed markdown answer.

        Query:
        {state['query']}

        Sources:
        {state['sources']}
        """
    )

    state["final_answer"] = response

    return state


def router(state: State) -> Literal[
    "search_node",
    "synthesis_node"
]:

    if state["satisfied"]:
        return "synthesis_node"

    if state["loop_count"] >= MAX_LOOPS:
        return "synthesis_node"

    return "search_node"


graph = StateGraph(State)

graph.add_node("search_node", search_node)
graph.add_node("reflection_node", reflection_node)
graph.add_node("synthesis_node", synthesis_node)

graph.add_edge(START, "search_node")
graph.add_edge("search_node", "reflection_node")

graph.add_conditional_edges(
    "reflection_node",
    router
)

graph.add_edge("synthesis_node", END)

app = graph.compile()