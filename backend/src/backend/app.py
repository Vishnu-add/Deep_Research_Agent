from fastapi import FastAPI, HTTPException
# from src.backend.api.routes import router
# from src.backend.config.settings import settings
from src.backend.utils.logger import setup_logger
from src.backend.agent import DeepResearchAgent
from src.backend.models.schemas import QuestionRequest, AnswerResponse, EvaluationRequest, EvaluationResult, BenchmarkRequest
from fastapi.responses import StreamingResponse
from langgraph.config import get_stream_writer
from src.backend.state import ResearchState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from langchain_core.messages import HumanMessage, SystemMessage
from src.backend.evaluate_agent import evaluate_agent 
from fastapi.middleware.cors import CORSMiddleware
import os
from langfuse import get_client
from langfuse.langchain import CallbackHandler
import uuid
from src.backend.architectures import ARCHITECTURES
import json

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
        config = {"configurable": {"thread_id": request.session_id}}
        initial_state = ResearchState(
            query=request.question,
            messages=[HumanMessage(content=request.question)],
            all_messages=[HumanMessage(content=request.question)],
            plan="",
            instructions="",
            subqueries=[],
            sources=[],
            validated_sources=[],
            reflection={},
            final_answer="",
            loop_count=1,
            session_id=request.session_id,
            model=request.model,
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
                if node_name == "synthesis_node" and messages and messages.content and isinstance(messages, AIMessage):
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


@app.post("/benchmark_agents")
async def benchmark_agents(request: BenchmarkRequest):

    try:

        benchmark_id = str(uuid.uuid4())

        asyncio.create_task(
            run_benchmark(benchmark_id, request.query)
        )
        
        return {
            "status": "success",
            "benchmark_id": benchmark_id,
            "message": f"Benchmarking Ongoing"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def run_benchmark(benchmark_id: str, query: str):
    results = {}

    logger.info(f"Starting benchmark with ID: {benchmark_id} for query: {query[:50]}...")
    for architecture_name, workflow in ARCHITECTURES.items():
        logger.info(f"Running architecture: {architecture_name} for benchmark ID: {benchmark_id}...")
        initial_state = {
            "query": query,

            "subqueries": [],

            "sources": [],

            "validated_sources": [],

            "reflection": {},

            "plan": "",

            "final_answer": "",

            "loop_count": 0,

            "satisfied": False
        }
        try:
            final_state = await workflow.ainvoke(initial_state)
        except Exception as e:
            logger.exception(f"Exception occurred while invoking workflow for architecture {architecture_name}: {e}")
            continue

        logger.info(f" {architecture_name} invocation Done.")

        logger.info(f"Evaluation triggered for architecture: {architecture_name} for benchmark ID: {benchmark_id}.")
        await evaluate_agent(
            state=final_state,
            architecture_name=architecture_name,
            session_id=benchmark_id
        )
        logger.info(f"Evaluation completed for architecture: {architecture_name} for benchmark ID: {benchmark_id}.")


        results[architecture_name] = {
            "status": "completed",
            "final_answer": final_state.get("final_answer", "")
        }
        logger.info(f"Completed architecture: {architecture_name} for benchmark ID: {benchmark_id}.")

    # =====================================================
    # YOUR PROPOSED AGENT
    # =====================================================

    deep_research_initial_state = {
        "query": query,

        "messages": [
            HumanMessage(content=query)
        ],

        "all_messages": [
            HumanMessage(content=query)
        ],

        "plan": "",

        "instructions": "",

        "subqueries": {},

        "sources": [],

        "validated_sources": [],

        "reflection": {},

        "final_answer": "",

        "loop_count": 1,

        "session_id": benchmark_id
    }

    config = {
        "configurable": {
            "thread_id": benchmark_id
        }
    }

    logger.info(f"Running our proposed agent for benchmark ID: {benchmark_id}...")
    deep_research_final_state = await deep_research_agent.workflow.ainvoke(
        deep_research_initial_state,
        config=config
    )
    logger.info(f"Our proposed agent invocation Done for benchmark ID: {benchmark_id}.")

    # =====================================================
    # EVALUATION OF YOUR AGENT
    # =====================================================
    logger.info(f"Evaluation triggered for our proposed agent for benchmark ID: {benchmark_id}.")
    await evaluate_agent(
        state=deep_research_final_state,
        architecture_name=deep_research_agent.name,
        session_id=benchmark_id
    )  
    logger.info(f"Evaluation completed for our proposed agent for benchmark ID: {benchmark_id}.")

    results[deep_research_agent.name] = {
        "status": "completed",
        "final_answer": deep_research_final_state.get(
            "final_answer",
            ""
        )
    }

    logger.info(f"Completed architecture: {deep_research_agent.name} for benchmark ID: {benchmark_id}.")

    ### Save the results to a JSON file
    os.makedirs("evaluation_results/benchmark_results", exist_ok=True)
    filename = f"evaluation_results/benchmark_results/{benchmark_id}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
    logger.info(f"Results saved to {filename}")
