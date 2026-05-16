from fastapi import FastAPI
# from src.backend.api.routes import router
# from src.backend.config.settings import settings
from src.backend.utils.logger import setup_logger
from src.backend.agent import DeepResearchAgent
from src.backend.models.schemas import QuestionRequest, AnswerResponse, EvaluationRequest, EvaluationResult

logger = setup_logger(__name__)

deep_research_agent = DeepResearchAgent()

app = FastAPI(
    title="Agentic Deep Research Assistant",
    description="Multi-hop question answering system for HotpotQA",
    version="1.0.0"
)

# Include routes
# app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Agentic Deep Research Assistant API", "status": "running"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the research assistant...")
    # Could add initialization logic here

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Answer a question using the research workflow."""
    try:
        logger.info(f"Processing question: {request.question[:50]}...")
        
        result = await deep_research_agent.run(request.question, request.max_iterations)
        logger.info("Question answered successfully")
        logger.info(f"Answer: {result.get('final_answer', '')[:50]}..., Confidence: {result.get('confidence_score', 0.0):.2f}")
        return result.get('final_answer', 'NO ANSWER GENERATED')
        
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the research assistant...")