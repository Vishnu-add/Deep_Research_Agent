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


def answer_node(state: State):

    query = state["query"]

    response = invoke_llm(
        "You are a deep research assistant.",
        f"""
        Answer the query in detail.

        Query:
        {query}
        """
    )

    state["final_answer"] = response

    return state


graph = StateGraph(State)

graph.add_node(
    "answer_node",
    answer_node
)

graph.add_edge(
    START,
    "answer_node"
)

graph.add_edge(
    "answer_node",
    END
)

app = graph.compile()