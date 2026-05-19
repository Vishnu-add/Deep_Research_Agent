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
    DECOMPOSER_PROMPT_ITER_2,
    USER_DECOMPOSER_PROMPT_ITER_2,
    SOURCE_VALIDATION_PROMPT,
    USER_VALIDATION_PROMPT,
    REFLECTION_PROMPT,
    USER_REFLECTION_PROMPT,
    SYNTHESIS_PROMPT
)
from src.backend.tools import (
    DECOMPOSER_TOOL,
    DECOMPOSER_TOOL_ITER_2,
    SOURCE_VALIDATION_TOOL,
    REFLECTION_TOOL,
)
from src.backend.stream_messages import (
    PLANNER_MESSAGES,
    DECOMPOSER_MESSAGES,
    SEARCH_MESSAGES,
    VALIDATION_MESSAGES,
    REFLECTION_MESSAGES,
    SYNTHESIS_MESSAGES
)
from src.backend.state import ResearchState
from langgraph.config import get_stream_writer

from langfuse import get_client
from langfuse.langchain import CallbackHandler
import os
import random

LANGFUSE_SECRET_KEY="sk-lf-f3310337-d8ec-4364-84ac-1668d59ba380"
LANGFUSE_PUBLIC_KEY="pk-lf-2c8a83a3-a53f-44ea-a333-0730ecadc80b"
LANGFUSE_BASE_URL="https://us.cloud.langfuse.com"

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
MAX_LOOPS = 3
RELEVANCE_THRESHOLD = 8
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUT_DIR = "outputs/final_answers"
os.makedirs(OUT_DIR, exist_ok=True)


def save_json(path, data):
    with open(path, "a", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


logger = setup_logger(__name__)

class DeepResearchAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model=MODEL_NAME,
            temperature=TEMPERATURE
        )
        # self.llm = 

        self.writer = None

        self.search_tool = DuckDuckGoSearchResults(
            num_results=MAX_SEARCH_RESULTS
        )
        self.workflow = self._build_workflow()
        self.workflow.get_graph().draw_mermaid_png(output_file_path="graph.png")
        logger.info("Workflow graph visualization saved as graph.png")

    def _llm(self, state: ResearchState):
        """Build a ChatOllama for this run, using the model picked by the caller
        (state['model']) or falling back to MODEL_NAME."""
        name = state.get("model") or MODEL_NAME
        return ChatOllama(model=name, temperature=TEMPERATURE)



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
        self.writer = get_stream_writer()
        
        session_folder = f"{OUTPUT_DIR}/session_{state['session_id']}"
        os.makedirs(session_folder, exist_ok=True)
        state["session_folder"] = session_folder

        # self.writer({"status": "Planning the research approach..."})
        self.writer({"status": random.choice(PLANNER_MESSAGES)})
        logger.info("Planning the research approach...")
        logger.info(f"=== PLANNING NODE {state['loop_count']} === ")
        #logger.info(f"Current state:{state}")
        messages = [
            SystemMessage(content=PLANNER_PROMPT),
            HumanMessage(content=state["query"]),
        ]

        # self.writer({"status": "Invoking the planner agent..."})
        logger.info(f"Invoking planner agent")
        response = self._llm(state).invoke(messages)

        # logger.info(f"Planning response:{response}")
        self.writer({"status": "Planning completed."})
        
        session_folder = state["session_folder"]        

        filename = f"{session_folder}/A5_planned_plan.json"
        save_json(
            filename,
            {"plan": response.content}
        )

        state["plan"] = response.content
        state["all_messages"] = state["all_messages"] + messages + [response]        
        return state
    
    def decomposer_node(self, state: ResearchState):
        """Takes the research plan and decomposes it into focused subqueries."""
        logger.info(f"=== DECOMPOSER NODE {state['loop_count']} ===")
        #logger.info(f"Current state:{state}")
        self.writer = get_stream_writer()
        self.writer({"status": random.choice(DECOMPOSER_MESSAGES)})

        if state["loop_count"] == 1:
            logger.info(f"Using initial decomposition without reflection instructions.")
            messages = [
                SystemMessage(content=DECOMPOSER_PROMPT),
                HumanMessage(content=USER_DECOMPOSER_PROMPT.format(plan=state["plan"])),
            ]
            llm_tool = self._llm(state).bind_tools([DECOMPOSER_TOOL], tool_choice="required")
        else:
            logger.info(f"Using instructions from reflection to guide decomposition: {state['instructions']}")
            messages = [
                SystemMessage(content=DECOMPOSER_PROMPT_ITER_2.format(instructions=state["instructions"])),
                HumanMessage(content=USER_DECOMPOSER_PROMPT_ITER_2.format(plan=state["plan"], existing_subquestions=state["subqueries"])),
            ]
            llm_tool = self._llm(state).bind_tools([DECOMPOSER_TOOL_ITER_2], tool_choice="required")

        response = None
        for i in range(3):
            response = llm_tool.invoke(messages)

            tool_calls = response.tool_calls
            response_content = response.content
            # logger.info(f"Decomposition response:{response.tool_calls}")

            if tool_calls:
                break

            if not tool_calls and not response_content:
                logger.info(f"No decomposition response received.")
                # continue
        if response is None or response.tool_calls is None or len(response.tool_calls) == 0:
            logger.info(f"No decomposition response received after multiple attempts.")
            self.writer({"status": "Decomposition completed."})
            return {
                "subqueries": state["subqueries"],
                "new_subqueries": [],
            }

        sub_queries = response.tool_calls[0].get("args", {}).get("subqueries", [])
        # Smaller models occasionally return subqueries as a string or another
        # non-list shape; coerce to a list so state concatenation stays safe.
        if isinstance(sub_queries, str):
            sub_queries = [sub_queries]
        elif not isinstance(sub_queries, list):
            sub_queries = []

        self.writer({"status": "Decomposition completed."})

        session_folder = state["session_folder"]        

        filename = f"{session_folder}/A5_decomposed_subqueries.json"
        save_json(
            filename,
            sub_queries
        )

        return {
            "subqueries": state["subqueries"] + sub_queries,
            "new_subqueries": sub_queries,
            "all_messages": state["all_messages"] + messages + [response]
        }

    def search_node(self, state: ResearchState):
        """Executes the search for each subquery and retrieves relevant sources."""
        self.writer = get_stream_writer()
        self.writer({"status": random.choice(SEARCH_MESSAGES)})
        logger.info(f"=== SEARCH NODE {state['loop_count']} ===")
        #logger.info(f"Current state:{state}")

        all_sources = []

        counter = 0

        for q in state["new_subqueries"]:

            try:

                results = self.search_tool.run(str(q))

            except Exception as e:

                results = str(e)

            all_sources.append({
                "question": q,
                "question_id": f"state['loop_count']_{counter}",
                "sources": results
            })
            counter += 1

        # state["sources"] = all_sources

        session_folder = state["session_folder"]        

        filename = f"{session_folder}/A5_raw_sources.json"
        save_json(
            filename,
            all_sources
        )

        return {
            "sources": state["sources"] + all_sources,
            "new_sources": all_sources,
        }
    
    
    def validation_node(self, state: ResearchState):
        """Validates the relevance of retrieved sources and filters them based on a relevance threshold."""

        # Curretly validating all sources, but ideally we should only validate a subset to save costs
        # And validating one by one, but ideally we could batch them
        logger.info(f"=== VALIDATION NODE {state['loop_count']} ===")
        #logger.info(f"Current state:{state}")
        self.writer = get_stream_writer()
        self.writer({"status": random.choice(VALIDATION_MESSAGES)})


        llm_tool = self._llm(state).bind_tools([SOURCE_VALIDATION_TOOL], tool_choice="required")

        if len(state["new_sources"]) > 5:
            state["new_sources"] = state["new_sources"][:5]

        messages = [
            SystemMessage(content=SOURCE_VALIDATION_PROMPT),
            HumanMessage(content=USER_VALIDATION_PROMPT.format(srcs=state["new_sources"], question=state["query"]))
        ]
        response = None
        for i in range(3):
            response = llm_tool.invoke(messages)

            tool_calls = response.tool_calls
            response_content = response.content
            # logger.info(f"Validation response:{response.tool_calls}")
            # logger.info(f"Validation response content:{response.content}")

            if tool_calls:
                break
            
            if not tool_calls and not response_content:
                logger.info(f"No validation response received.")
                # continue
        if response is None or response.tool_calls is None or len(response.tool_calls) == 0:
            logger.info(f"No response received after multiple attempts.")
            return {
                "validated_sources": state["sources"],
                "new_validated_sources": state["sources"]
            }

        parsed = response.tool_calls[0].get("args", {}).get("questions_with_scores", [])

        # logger.info(f"Parsed validation:{parsed}")

        filtered_question_ids = []
        filtered_sources = []

        for item in parsed:
            # Smaller models occasionally return malformed entries; skip anything
            # that is not a dict with the expected fields.
            if not isinstance(item, dict):
                continue
            score = item.get("score")
            if isinstance(score, (int, float)) and score >= RELEVANCE_THRESHOLD:
                filtered_question_ids.append(item.get("question_id"))

        for src in state["new_sources"]:
            if src["question_id"] in filtered_question_ids:
                filtered_sources.append(src)

        # state["validated_sources"] = filtered_sources

        session_folder = state["session_folder"]        

        filename = f"{session_folder}/A5_validation.json"
        save_json(
            filename,
            filtered_sources
        )

        return {
            "validated_sources": state["validated_sources"] + filtered_sources,
            "new_validated_sources": filtered_sources,
            "all_messages": state["all_messages"] + messages + [response]
        }

    def reflection_node(self, state: ResearchState):
        

        logger.info(f"=== REFLECTION NODE {state['loop_count']} ===")
        #logger.info(f"Current state:{state}")
        self.writer = get_stream_writer()
        self.writer({"status": random.choice(REFLECTION_MESSAGES)})

        if state["loop_count"] >= MAX_LOOPS:
            logger.info(f"Maximum loop count reached. No further reflection.")
            state["loop_count"] += 1
            return state

        llm_tool = self._llm(state).bind_tools([REFLECTION_TOOL], tool_choice="required")

        messages = [
            SystemMessage(content=REFLECTION_PROMPT),
            HumanMessage(content=USER_REFLECTION_PROMPT.format(query=state["query"], plan=state["plan"], validated_sources=state["new_validated_sources"]))
        ]

        response = None
        for i in range(3):
            response = llm_tool.invoke(messages)

            tool_calls = response.tool_calls
            response_content = response.content
            # logger.info(f"Reflection response:{response.tool_calls}")
            # logger.info(f"Reflection response content:{response.content}")

            if tool_calls:
                break
            
            if not tool_calls and not response_content:
                logger.info(f"No reflection response received.")
                # continue
        if response is None or response.tool_calls is None or len(response.tool_calls) == 0:
            logger.info(f"No reflection response received after multiple attempts.")
            state["loop_count"] += 1
            return state
            # return Command(
            #     name="no_reflection_response",
            #     args={}
            # )
        # response = llm_tool.invoke(messages)

        # logger.info(f"Reflection response:{response.tool_calls}")

        parsed = response.tool_calls[0].get("args", {})

        state["reflection"] = parsed

        state["instructions"] = parsed[
            "instructions"
        ]

        state["loop_count"] += 1

        state["all_messages"] = state["all_messages"] + messages + [response]

        session_folder = state["session_folder"]        

        filename = f"{session_folder}/A5_reflection.json"
        save_json(
            filename,
            parsed
        )

        return state
    
    def synthesis_node(self,state: ResearchState):
        USER_PROMPT = """
        Query:
        {query}
        Validated Sources:
        {validated_sources}
        """
        logger.info(f"=== SYNTHESIS NODE {state['loop_count']} ===")
        #logger.info(f"Current state:{state}")
        self.writer = get_stream_writer()
        self.writer({"status": random.choice(SYNTHESIS_MESSAGES)})
        messages = [
            SystemMessage(content=SYNTHESIS_PROMPT),
            HumanMessage(content=USER_PROMPT.format(query=state["query"], validated_sources=state["validated_sources"]))
        ]
        response = self._llm(state).invoke(messages)

        state["final_answer"] = response.content

        state["messages"] = state["messages"] + [response]

        state["all_messages"] = state["all_messages"] + messages + [response]

        # self.writer({"status": "Saving the final answer..."})
        logger.info(f"Synthesis completed. Final answer generated.")
        filename = f"{OUT_DIR}/final_answer_{state['session_id']}.md"

        # Saving the final answer in the markdown file 
        with open(filename, "w") as f:
            f.write(state["final_answer"])

        return state

        
    def router(self, state: ResearchState) -> Literal[
        "decomposer_node",
        "synthesis_node"
    ]:
        logger.info(f"=== ROUTER {state['loop_count']} ===")
        #logger.info(f"Current state:{state}")
        self.writer = get_stream_writer()

        if state["loop_count"] >= MAX_LOOPS+1:
            self.writer({"status": "Maximum loop count reached. Proceeding to synthesis."})
            return "synthesis_node"

        if state["reflection"].get("info_needed", False):
            self.writer({"status": "More information needed. Looping back to decomposer."})
            return "decomposer_node"

        self.writer({"status": "No more information needed. Proceeding to synthesis."})
        return "synthesis_node"

    async def run(self, question: str, max_iterations: int = 3, session_id: str = "1") -> Dict[str, Any]:
        """Run the research workflow."""
        initial_state = ResearchState(
            query=question,
            messages=[HumanMessage(content=question)],
            all_messages=[HumanMessage(content=question)],
            plan="",
            instructions="",
            subqueries=[],
            sources=[],
            validated_sources=[],
            reflection={},
            final_answer="",
            loop_count=1,
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
        