from typing import TypedDict, List, Dict, Any, Optional
import operator
from typing import Annotated

class ResearchState(TypedDict):
    query: str
    messages: list
    all_messages: list
    plan : str
    instructions: str
    subqueries: list
    new_subqueries: list
    sources: dict
    new_sources: list
    validated_sources: list
    new_validated_sources: list
    reflection: dict
    final_answer: str
    loop_count: int
    session_id: str
    session_folder: str
    model: Optional[str]

    next_node: Annotated[list, operator.add]
    prev_node: Annotated[list, operator.add]
    info_to_planner: Optional[Dict[str, Any]]
    tools_needed: list
    web_search_queries : list
    scientific_search_queries : list
    wiki_search_queries : list

    web_search_all_sources : list
    new_web_search_sources : list

    scientific_search_all_sources : list
    new_scientific_search_sources : list

    wikipedia_search_all_sources : list
    new_wikipedia_search_sources : list
    loop_node: str
    direct_answer: str


# class ResearchState(TypedDict):
#     question: str
#     sub_questions: List[str]
#     current_sub_question: Optional[str]
#     retrieved_docs: List[Dict[str, Any]]
#     verified_docs: List[Dict[str, Any]]
#     reasoning_trace: List[Dict[str, Any]]
#     final_answer: Optional[str]
#     confidence_score: float
#     iteration_count: int
#     max_iterations: int
#     reflection_decision: Optional[str]
#     suggested_queries: List[str]