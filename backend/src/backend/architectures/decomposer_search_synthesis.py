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


def decomposer_node(state: State):

    query = state["query"]

    response = invoke_llm(
        "You are a decomposition agent.",
        f"""
        Break the query into smaller focused research questions.

        Return STRICT JSON LIST.

        Query:
        {query}
        """
    )

    parsed = extract_json(response)

    if parsed is None:
        parsed = [query]

    state["subqueries"] = parsed

    try:
        state["plan"] = "\n".join(parsed)
    except Exception as e:
        state["plan"] = str(parsed)
        print(f"Exception occurred while creating plan: {e}")

    return state


def search_node(state: State):

    subqueries = state["subqueries"]

    all_sources = []

    for q in subqueries:

        results = search_tool.run(str(q))

        all_sources.append({
            "question": q,
            "sources": results
        })

    state["sources"] = all_sources

    state["validated_sources"] = all_sources

    return state


def synthesis_node(state: State):

    response = invoke_llm(
        "You are a synthesis agent.",
        f"""
        Generate a detailed markdown report.

        Query:
        {state['query']}

        Sources:
        {state['sources']}
        """
    )

    state["final_answer"] = response

    return state


graph = StateGraph(State)

graph.add_node("decomposer_node", decomposer_node)
graph.add_node("search_node", search_node)
graph.add_node("synthesis_node", synthesis_node)

graph.add_edge(START, "decomposer_node")
graph.add_edge("decomposer_node", "search_node")
graph.add_edge("search_node", "synthesis_node")
graph.add_edge("synthesis_node", END)

app = graph.compile()
app.get_graph().draw_mermaid_png(output_file_path="decomposer_search_synthesis.png")