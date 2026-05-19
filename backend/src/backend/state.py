from typing import TypedDict, List, Dict, Any, Optional


class ResearchState(TypedDict):
    query: str
    messages: list
    all_messages: list
    plan : str
    instructions: str
    subqueries: list
    new_subqueries: list
    sources: list
    new_sources: list
    validated_sources: list
    new_validated_sources: list
    reflection: dict
    final_answer: str
    loop_count: int
    session_id: str
    session_folder: str
    model: Optional[str]

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