from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, START, END

from src.backend.common_utils import *


class State(TypedDict):

    query: str

    subqueries: List[str]

    sources: List[Any]

    validated_sources: List[Any]

    reflection: Dict[str, Any]

    plan: str

    final_answer: str

    loop_count: int


def search_node(state: State):

    query = state["query"]

    results = search_tool.run(query)

    state["sources"] = [results]

    state["validated_sources"] = [results]

    return state


def synthesis_node(state: State):

    query = state["query"]

    sources = state["sources"]

    response = invoke_llm(
        "You are a deep research assistant.",
        f"""
        Generate a detailed markdown report.

        Query:
        {query}

        Sources:
        {sources}
        """
    )

    state["final_answer"] = response

    return state


graph = StateGraph(State)

graph.add_node(
    "search_node",
    search_node
)

graph.add_node(
    "synthesis_node",
    synthesis_node
)

graph.add_edge(
    START,
    "search_node"
)

graph.add_edge(
    "search_node",
    "synthesis_node"
)

graph.add_edge(
    "synthesis_node",
    END
)

app = graph.compile()