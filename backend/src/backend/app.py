from fastapi import FastAPI
# from src.backend.api.routes import router
# from src.backend.config.settings import settings
from src.backend.utils.logger import setup_logger
from src.backend.agent import DeepResearchAgent
from src.backend.models.schemas import QuestionRequest, AnswerResponse, EvaluationRequest, EvaluationResult
from fastapi.responses import StreamingResponse
from langgraph.config import get_stream_writer
from src.backend.state import ResearchState
from langchain_core.messages import HumanMessage, SystemMessage
from src.backend.evaluate_agent import evaluate_agent 
from fastapi.middleware.cors import CORSMiddleware
import os
from langfuse import get_client
from langfuse.langchain import CallbackHandler

LANGFUSE_SECRET_KEY="sk-lf-f3310337-d8ec-4364-84ac-1668d59ba380"
LANGFUSE_PUBLIC_KEY="pk-lf-2c8a83a3-a53f-44ea-a333-0730ecadc80b"
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"


os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_BASE_URL"] = LANGFUSE_BASE_URL

# Initialize Langfuse client
langfuse = get_client()
langfuse_handler = CallbackHandler()


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


@app.post("/get_stream")
async def get_stream(request: QuestionRequest):
    try:
        config = {
            "configurable": {"thread_id": request.session_id},
            "callbacks": [langfuse_handler]
        }
        initial_state = ResearchState(
            query=request.question,
            messages=[HumanMessage(content=request.question)],
            all_messages=[HumanMessage(content=request.question)],
            plan="",
            instructions="",
            subqueries={},
            sources=[],
            validated_sources=[],
            reflection={},
            final_answer="",
            loop_count=1,
            session_id=request.session_id
        )

        async for chunk in deep_research_agent.workflow.astream(
            # {"query": request.question, "max_iterations": request.max_iterations, "session_id": request.session_id},
            initial_state,
            config=config,
            stream_mode=["custom", "messages"],
            version="v2", 
        ):
            if chunk.get("type") == "custom":
                logger.info(f"Streaming custom event: {chunk.get('data',{}).get('status', '')}")
                # yield chunk.get("data", {}).get("status")
                yield {
                    "type": "thinking",
                    "description": chunk.get("data", {}).get("status", "")
                }
                chunk.get("data", {}).get("status")
            elif chunk.get("type") == "messages":
                # logger.info(f"Streaming messages")
                chunk_data = chunk.get("data", ())
                messages = chunk_data[0] if len(chunk_data) > 0 else None
                node_name = chunk_data[1].get("langgraph_node", "") if len(chunk_data) > 1 else ""
                if node_name == "synthesis_node" and messages and messages.content:
                    # logger.info(f"Streaming message content: {chunk_data[0].content[:50]}...")
                    # yield chunk_data[0].content
                    yield {
                        "type": "final_answer",
                        "description": chunk_data[0].content
                    }

        logger.info("Streaming completed.")
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
        yield f"Error: {str(e)}"

    try:
        logger.info("In evaluation")
        config = {"configurable": {"thread_id": request.session_id}}
        state = deep_research_agent.workflow.get_state(config=config)
        state_values = state.values
        # logger.info(f"State Values : {state_values}")
        
        if state_values:
            asyncio.create_task(
                evaluate_agent(state_values, deep_research_agent.name, request.session_id)
            )
            # asyncio.run(evaluate_agent(state_values, deep_research_agent.name, request.session_id))
        else:
            logger.info(f"No State values, SKIPPING evaluation!")

    except Exception as e:
        logger.exception(f"Exception while evaluating agent: {e}")
    

import asyncio
@app.post("/evaluate")
async def evaluate(request: EvaluationRequest):
    logger.info("In evaluation")
    try:
        config = {"configurable": {"thread_id": request.session_id}}
        state = deep_research_agent.workflow.get_state(config=config)
        state_values = state.values
        logger.info(f"State Values : {state_values}")
        
        if state_values:
            asyncio.create_task(
                evaluate_agent(state_values, deep_research_agent.name, request.session_id)
            )
            # asyncio.run(evaluate_agent(state_values, deep_research_agent.name, request.session_id))
        else:
            logger.info(f"No State values, SKIPPING evaluation!")
        return {
            "status": "success",
            "message": "Evaluation Ongoing"
        }

    except Exception as e:
        logger.exception(f"Exception while evaluating agent: {e}")

        raise HTTPException(
            status_code=500,
            detail="Error occurred during evaluation"
        )
    

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the research assistant...")