from fastapi import FastAPI
# from src.backend.api.routes import router
# from src.backend.config.settings import settings
from src.backend.utils.logger import setup_logger
from src.backend.agent import DeepResearchAgent
from src.backend.models.schemas import QuestionRequest, AnswerResponse, EvaluationRequest, EvaluationResult
from fastapi.responses import StreamingResponse
from langgraph.config import get_stream_writer
from langgraph.stream import ProtocolEvent, StreamChannel, StreamTransformer

# 1. Custom transformer to collect events
class CustomTransformer(StreamTransformer):
    required_stream_modes = ("custom",)

    def __init__(self, scope: tuple[str, ...] = ()) -> None:
        super().__init__(scope)
        self.log = StreamChannel()

    def init(self) -> dict:
        return {"custom": self.log}

    def process(self, event: ProtocolEvent) -> bool:
        if event["method"] == "custom":
            self.log.push(event["params"]["data"])
        return True

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

@app.post("/stream")
async def stream_data(request: QuestionRequest):
    config = {"configurable": {"thread_id": request.session_id}}
    async def generate():
        # Start streaming
        stream = await deep_research_agent.workflow.astream_events(
            {"query": request.question, "max_iterations": request.max_iterations},
            version="v3", 
            config=config,
            transformers=[CustomTransformer]
        )
        
        # Stream custom events as they happen
        async for item in stream.extensions["custom"]:
            yield f"data: {item}\n\n"
            
        # Await final output
        final = await stream.output
        yield f"data: final:{final}\n\n"
        
    return StreamingResponse(generate(), media_type="text/event-stream")



@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the research assistant...")