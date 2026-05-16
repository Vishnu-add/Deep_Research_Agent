from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5

class VerificationRequest(BaseModel):
    evidence: List[Dict[str, Any]]
    question: str

class SynthesisRequest(BaseModel):
    question: str
    verified_evidence: List[Dict[str, Any]]
    reasoning_trace: List[Dict[str, Any]]