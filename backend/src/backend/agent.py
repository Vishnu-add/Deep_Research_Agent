import os
import re
import json
from datetime import datetime
from typing import List, Dict, Any

from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from src.backend.utils.logger import setup_logger
from typing import TypedDict, Literal
from langgraph.checkpoint.memory import InMemorySaver  
from langgraph.graph import StateGraph, START, END
from src.backend.prompts import (
    PLANNER_PROMPT,
    DECOMPOSER_PROMPT,
    USER_DECOMPOSER_PROMPT,
    SOURCE_VALIDATION_PROMPT,
    USER_VALIDATION_PROMPT,
    REFLECTION_PROMPT,
    SYNTHESIS_PROMPT
)
from src.backend.tools import (
    DECOMPOSER_TOOL,
    SOURCE_VALIDATION_TOOL,
    REFLECTION_TOOL,
)
from src.backend.state import ResearchState
from langgraph.config import get_stream_writer

from langfuse import get_client
from langfuse.langchain import CallbackHandler
import os

os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_BASE_URL"] = LANGFUSE_BASE_URL

# Initialize Langfuse client
langfuse = get_client()

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

from langfuse.langchain import CallbackHandler
from langfuse import observe
# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")


MODEL_NAME = "qwen3:8b"
TEMPERATURE = 0
MAX_SEARCH_RESULTS = 5
MAX_LOOPS = 1
RELEVANCE_THRESHOLD = 8
OUT_DIR = "outputs/final_answers"
os.makedirs(OUT_DIR, exist_ok=True)



logger = setup_logger(__name__)

class DeepResearchAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model=MODEL_NAME,
            temperature=TEMPERATURE
        )
        # self.llm = 

        self.search_tool = DuckDuckGoSearchResults(
            num_results=MAX_SEARCH_RESULTS
        )
        self.writer = None
        self.workflow = self._build_workflow()
        self.workflow.get_graph().draw_mermaid_png(output_file_path="graph.png")
        logger.info("Workflow graph visualization saved as graph.png")

    
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        graph = StateGraph(ResearchState)

                
        graph.add_node(
            "planner_node",
            self.planner_node
        )

        graph.add_node(
            "decomposer_node",
            self.decomposer_node
        )

        graph.add_node(
            "search_node",
            self.search_node
        )

        graph.add_node(
            "validation_node",
            self.validation_node
        )

        graph.add_node(
            "reflection_node",
            self.reflection_node
        )

        graph.add_node(
            "synthesis_node",
            self.synthesis_node
        )

        # ============================================================
        # FLOW
        # ============================================================

        graph.add_edge(
            START,
            "planner_node"
        )

        graph.add_edge(
            "planner_node",
            "decomposer_node"
        )

        graph.add_edge(
            "decomposer_node",
            "search_node"
        )

        graph.add_edge(
            "search_node",
            "validation_node"
        )

        graph.add_edge(
            "validation_node",
            "reflection_node"
        )

        graph.add_conditional_edges(
            "reflection_node",
            self.router
        )

        graph.add_edge(
            "synthesis_node",
            END
        )

        # ============================================================
        # COMPILE
        # ============================================================
        checkpointer = InMemorySaver()

        workflow = graph.compile(checkpointer=checkpointer)

        return workflow
    
    def planner_node(self, state: ResearchState):
        """
        Takes the initial query and generates a step-by-step research plan.
        """
        if self.writer is None:
            logger.warning("Stream writer not initialized. Initializing now.")
            self.writer = get_stream_writer()
        self.writer({"status": "Planning the research approach..."})
        logger.info("Planning the research approach...")
        logger.info(f"=== PLANNING NODE ===")
        #logger.info(f"Current state:{state}")
        messages = [
            SystemMessage(content=PLANNER_PROMPT),
            HumanMessage(content=state["query"]),
        ]

        self.writer({"status": "Invoking the planner agent..."})
        logger.info(f"Invoking planner agent")
        response = self.llm.invoke(messages)

        # logger.info(f"Planning response:{response}")
        self.writer({"status": "Planning completed."})

        state["plan"] = response.content
        state["messages"] = messages + [response]
        
        return state
    
    def decomposer_node(self, state: ResearchState):
        """Takes the research plan and decomposes it into focused subqueries."""
        logger.info(f"=== DECOMPOSER NODE ===")
        #logger.info(f"Current state:{state}")

        messages = [
            SystemMessage(content=DECOMPOSER_PROMPT),
            HumanMessage(content=USER_DECOMPOSER_PROMPT.format(plan=state["plan"])),
        ]
        llm_tool = self.llm.bind_tools([DECOMPOSER_TOOL], tool_choice="required")
        response = llm_tool.invoke(messages)

        logger.info(f"Decomposition response:{response.tool_calls}")

        sub_queries = response.tool_calls[0].get("args", {}).get("subqueries", [])

        self.writer({"status": "Decomposition completed."})

        return {
            "subqueries": sub_queries,
            "messages": response    
        }

    def search_node(self, state: ResearchState):
        """Executes the search for each subquery and retrieves relevant sources."""
        self.writer({"status": "Searching for information..."})
        logger.info(f"=== SEARCH NODE ===")
        #logger.info(f"Current state:{state}")

        all_sources = []

        counter = 0

        for q in state["subqueries"]:

            try:

                results = self.search_tool.run(str(q))

            except Exception as e:

                results = str(e)

            all_sources.append({
                "question": q,
                "question_id": counter,
                "sources": results
            })
            counter += 1

        # state["sources"] = all_sources

        # save_json(
        #     "outputs/logs/A5_raw_sources.json",
        #     all_sources
        # )

        return {
            "sources": all_sources
        }
    
    
    def validation_node(self, state: ResearchState):
        """Validates the relevance of retrieved sources and filters them based on a relevance threshold."""

        # Curretly validating all sources, but ideally we should only validate a subset to save costs
        # And validating one by one, but ideally we could batch them
        logger.info(f"=== VALIDATION NODE ===")
        #logger.info(f"Current state:{state}")
        self.writer({"status": "Validating retrieved sources..."})


        llm_tool = self.llm.bind_tools([SOURCE_VALIDATION_TOOL], tool_choice="required")

        if len(state["sources"]) > 5:
            state["sources"] = state["sources"][:5]

        messages = [
            SystemMessage(content=SOURCE_VALIDATION_PROMPT),
            HumanMessage(content=USER_VALIDATION_PROMPT.format(srcs=state["sources"], question=state["query"]))
        ]
        response = None
        for i in range(3):
            response = llm_tool.invoke(messages)

            tool_calls = response.tool_calls
            response_content = response.content
            logger.info(f"Validation response:{response.tool_calls}")
            logger.info(f"Validation response content:{response.content}")

            if tool_calls:
                break
            
            if not tool_calls and not response_content:
                logger.info(f"No validation response received.")
                # continue
        if response is None or response.tool_calls is None or len(response.tool_calls) == 0:
            logger.info(f"No response received after multiple attempts.")
            return {
                "validated_sources": state["sources"]
            }

        parsed = response.tool_calls[0].get("args", {}).get("questions_with_scores", [])

        logger.info(f"Parsed validation:{parsed}")

        filtered_question_ids = []
        filtered_sources = []

        for item in parsed:
            if item["score"] >= RELEVANCE_THRESHOLD:
                filtered_question_ids.append(item["question_id"])

        for src in state["sources"]:
            if src["question_id"] in filtered_question_ids:
                filtered_sources.append(src)

        # state["validated_sources"] = filtered_sources

        # save_json(
        #     "outputs/validation/A5_validation.json",
        #     filtered_sources
        # )

        return {
            "validated_sources": filtered_sources
        }
    
    



    def reflection_node(self, state: ResearchState):
        USER_PROMPT = """
        Query:
        {query}
        Validated Sources:
        {validated_sources}
        """

        logger.info(f"=== REFLECTION NODE ===")
        #logger.info(f"Current state:{state}")
        self.writer({"status": "Reflecting on the research process..."})

        llm_tool = self.llm.bind_tools([REFLECTION_TOOL], tool_choice="required")

        messages = [
            SystemMessage(content=REFLECTION_PROMPT),
            HumanMessage(content=USER_PROMPT.format(query=state["query"], validated_sources=state["validated_sources"]))
        ]
        response = llm_tool.invoke(messages)

        logger.info(f"Reflection response:{response.tool_calls}")

        parsed = response.tool_calls[0].get("args", {})

        state["reflection"] = parsed

        state["instructions"] = parsed[
            "instructions"
        ]

        state["loop_count"] += 1

        # save_json(
        #     "outputs/reflection/A5_reflection.json",
        #     parsed
        # )

        return state
    
    


    def synthesis_node(self,state: ResearchState):
        USER_PROMPT = """
        Query:
        {query}
        Validated Sources:
        {validated_sources}
        """
        logger.info(f"=== SYNTHESIS NODE ===")
        #logger.info(f"Current state:{state}")
        self.writer({"status": "Synthesizing the final answer..."})
        messages = [
            SystemMessage(content=SYNTHESIS_PROMPT),
            HumanMessage(content=USER_PROMPT.format(query=state["query"], validated_sources=state["validated_sources"]))
        ]
        response = self.llm.invoke(messages)

        state["final_answer"] = response.content

        self.writer({"status": "Saving the final answer..."})
        filename = f"{OUT_DIR}/final_answer_{state['session_id']}.md"

        # Saving the final answer in the markdown file 
        with open(filename, "w") as f:
            f.write(state["final_answer"])

        return state

        
    def router(self, state: ResearchState) -> Literal[
        "decomposer_node",
        "synthesis_node"
    ]:
        logger.info(f"=== ROUTER ===")
        #logger.info(f"Current state:{state}")

        if state["loop_count"] >= MAX_LOOPS:
            return "synthesis_node"

        if state["reflection"]["info_needed"]:
            return "decomposer_node"

        return "synthesis_node"

    async def run(self, question: str, max_iterations: int = 3, session_id: str = "1") -> Dict[str, Any]:
        """Run the research workflow."""
        initial_state = ResearchState(
            query=question,
            messages=[],
            plan="",
            instructions="",
            subqueries=[],
            sources=[],
            validated_sources=[],
            reflection={},
            final_answer="",
            loop_count=0,
            session_id=session_id
        )

        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [langfuse_handler],
        }
        
        result = await self.workflow.ainvoke(initial_state, config)
        return result

        # for chunk in self.workflow.stream(
        #     initial_state,
        #     config,
        #     stream_mode=["updates", "custom"],
        #     version="v2"
        # ):
        #     # logger.info(f"Received chunk: {chunk}")
        #     if chunk["type"] == "updates":
        #         for node_name, state in chunk["data"].items():
        #             logger.info(f"Node {node_name} updated: state")
        #     elif chunk["type"] == "custom":
        #         logger.info(f"Status: {chunk['data']['status']}")
        