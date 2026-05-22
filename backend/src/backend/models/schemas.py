from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QuestionRequest(BaseModel):
    question: str
    max_iterations: Optional[int] = 3
    session_id: Optional[str] = "1"
    model: Optional[str] = None

class Evidence(BaseModel):
    title: str
    content: str
    score: float
    source: str

class ReasoningStep(BaseModel):
    step: str
    evidence: List[Evidence]
    reasoning: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    reasoning_trace: List[ReasoningStep]
    evidence: List[Evidence]

# class EvaluationRequest(BaseModel):
#     predictions: List[Dict[str, Any]]
#     ground_truth: List[Dict[str, Any]]
class EvaluationRequest(BaseModel):
    session_id: Optional[str] = "1"

class EvaluationResult(BaseModel):
    exact_match: float
    f1_score: float
    supporting_fact_em: float
    supporting_fact_f1: float

class BenchmarkRequest(BaseModel):
    query: str