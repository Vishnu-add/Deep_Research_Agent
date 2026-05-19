from src.backend.state import ResearchState
from src.backend.evaluation_prompts_tools import (
    CONTEXT_SYSTEM_PROMPT,
    CONTEXT_USER_PROMPT,
    ANSWER_SYSTEM_PROMPT,
    ANSWER_USER_PROMPT,
    FAITHFULNESS_SYSTEM_PROMPT,
    FAITHFULNESS_USER_PROMPT,
    DECOMPOSITION_SYSTEM_PROMPT,
    DECOMPOSITION_USER_PROMPT,
    REFLECTION_SYSTEM_PROMPT,
    REFLECTION_USER_PROMPT
)

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os
from src.backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# ============================================================
# MODEL
# ============================================================

MODEL_NAME = "qwen3:8b"
TEMPERATURE = 0

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    reasoning=False
)

# ============================================================
# ARCHITECTURES
# ============================================================

ARCHITECTURES = [
    "single_llm_call",
    "single_search_llm",
    "iterative_search_llm",
    "decomposer_search_synthesis",
    "full_reflective_architecture"
]

# ============================================================
# HELPER
# ============================================================

async def invoke_evaluator(
    system_prompt,
    user_prompt,
    tool_schema,
    tool_name
):
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    llm_tool = llm.bind_tools(
        [tool_schema],
        tool_choice="required"
    )
    try:
        response = llm_tool.invoke(messages)
    except Exception as e:
        return {
            "score": 0,
            "reason": f"Evaluation failed: {str(e)}"
        }

    if not response.tool_calls:
        return {
            "score": 0,
            "reason": "No evaluation generated"
        }

    args = response.tool_calls[0]["args"]

    return {
        "score": args.get("score", 0),
        "reason": args.get("reason", "")
    }

# ============================================================
# COMMON TOOL SCHEMA GENERATOR
# ============================================================

def create_metric_tool(
    tool_name,
    metric_name,
    metric_description
):
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": metric_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 10,
                        "description": f"{metric_name} score from 0 to 10"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Very short reason for the score"
                    }
                },
                "required": ["score", "reason"],
                "additionalProperties": False
            }
        }
    }

    
context_tool = create_metric_tool(
    tool_name="context_relevance_evaluation",
    metric_name="Context Relevance",
    metric_description="Evaluate context relevance quality"
)

answer_tool = create_metric_tool(
    tool_name="answer_relevance_evaluation",
    metric_name="Answer Relevance",
    metric_description="Evaluate answer relevance quality"
)

faithfulness_tool = create_metric_tool(
    tool_name="faithfulness_evaluation",
    metric_name="Faithfulness",
    metric_description="Evaluate groundedness and faithfulness"
)

decomposition_tool = create_metric_tool(
    tool_name="decomposition_evaluation",
    metric_name="Decomposition Quality",
    metric_description="Evaluate decomposition quality"
)

reflection_tool = create_metric_tool(
    tool_name="reflection_evaluation",
    metric_name="Reflection Quality",
    metric_description="Evaluate self correction quality"
)


# ============================================================
# MAIN EVALUATION FUNCTION
# ============================================================

async def evaluate_agent(
    state,
    architecture_name,
    session_id
):

    if architecture_name not in ARCHITECTURES:
        raise ValueError(
            f"Invalid architecture name: {architecture_name}"
        )

    # ========================================================
    # CONTEXT RELEVANCE
    # ========================================================

    if architecture_name == "single_llm_call":
        context_result = {
            "score": 0,
            "reason": "No retrieval used"
        }
    else:
        context_result = await invoke_evaluator(
            CONTEXT_SYSTEM_PROMPT,
            CONTEXT_USER_PROMPT.format(
                architecture=architecture_name,
                query=state.get("query", ""),
                subqueries=state.get("subqueries", []),
                sources=state.get("sources", []),
                validated_sources=state.get("validated_sources", []),
                final_answer=state.get("final_answer", "")
            ),
            context_tool,
            "context_relevance_evaluation"
        )

    # ========================================================
    # ANSWER RELEVANCE
    # ========================================================

    answer_result = await invoke_evaluator(
        ANSWER_SYSTEM_PROMPT,
        ANSWER_USER_PROMPT.format(
            architecture=architecture_name,
            query=state.get("query", ""),
            final_answer=state.get("final_answer", "")
        ),
        answer_tool,
        "answer_relevance_evaluation"
    )

    # ========================================================
    # FAITHFULNESS
    # ========================================================

    if architecture_name == "single_llm_call":
        faithfulness_result = {
            "score": 0,
            "reason": "No evidence grounding"
        }
    else:
        faithfulness_result = await invoke_evaluator(
            FAITHFULNESS_SYSTEM_PROMPT,
            FAITHFULNESS_USER_PROMPT.format(
                architecture=architecture_name,
                query=state.get("query", ""),
                sources=state.get("sources", []),
                validated_sources=state.get("validated_sources", []),
                final_answer=state.get("final_answer", "")
            ),
            faithfulness_tool,
            "faithfulness_evaluation"
        )

    # ========================================================
    # DECOMPOSITION QUALITY
    # ========================================================

    if architecture_name in [
        "single_llm_call",
        "single_search_llm",
        "iterative_search_llm"
    ]:
        decomposition_result = {
            "score": 0,
            "reason": "No decomposition used"
        }
    else:
        decomposition_result = await invoke_evaluator(
            DECOMPOSITION_SYSTEM_PROMPT,
            DECOMPOSITION_USER_PROMPT.format(
                architecture=architecture_name,
                query=state.get("query", ""),
                subqueries=state.get("subqueries", []),
                plan=state.get("plan", "")
            ),
            decomposition_tool,
            "decomposition_evaluation"
        )

    # ========================================================
    # REFLECTION QUALITY
    # ========================================================

    if architecture_name != "full_reflective_architecture":
        reflection_result = {
            "score": 0,
            "reason": "No reflection used"
        }
    else:
        reflection_result = await invoke_evaluator(
            REFLECTION_SYSTEM_PROMPT,
            REFLECTION_USER_PROMPT.format(
                architecture=architecture_name,
                query=state.get("query", ""),
                reflection=state.get("reflection", {}),
                loop_count=state.get("loop_count", 0),
                validated_sources=state.get("validated_sources", []),
                final_answer=state.get("final_answer", "")
            ),
            reflection_tool,
            "reflection_evaluation"
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    evaluation_result = {
        "architecture_name": architecture_name,

        "context_relevance": context_result,

        "answer_relevance": answer_result,

        "faithfulness_groundedness": faithfulness_result,

        "decomposition_quality": decomposition_result,

        "reflection_self_correction_quality": reflection_result
    }

    # return evaluation_result
    logger.info(f"Evaluation output : {evaluation_result}")

    ## write code to save json
    os.makedirs("evaluation_results", exist_ok=True)

    filename = (
        f"evaluation_results/"
        f"{architecture_name}_{session_id}.json"
    )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            evaluation_result,
            f,
            indent=4,
            ensure_ascii=False
        )

    logger.info(f"Evaluation saved to {filename}")



