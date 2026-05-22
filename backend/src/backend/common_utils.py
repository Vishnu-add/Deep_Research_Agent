import os
import re
import json
from datetime import datetime

from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import HumanMessage, SystemMessage

MODEL_NAME = "qwen3:8b"
TEMPERATURE = 0
MAX_SEARCH_RESULTS = 5

BASE_OUTPUT = "outputs"

DIRS = {
    "reports": os.path.join(BASE_OUTPUT, "reports"),
    "metrics": os.path.join(BASE_OUTPUT, "metrics"),
    "graphs": os.path.join(BASE_OUTPUT, "graphs"),
    "decomposition": os.path.join(BASE_OUTPUT, "decomposition"),
    "validation": os.path.join(BASE_OUTPUT, "validation"),
    "reflection": os.path.join(BASE_OUTPUT, "reflection"),
    "logs": os.path.join(BASE_OUTPUT, "logs")
}

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    reasoning=False
)

search_tool = DuckDuckGoSearchResults(
    num_results=MAX_SEARCH_RESULTS
)


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_text(path, text):

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def invoke_llm(system_prompt, human_prompt):

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]

    response = llm.invoke(messages)

    return response.content


def extract_json(text):

    try:

        match = re.search(
            r"\{.*\}|\[.*\]",
            text,
            re.DOTALL
        )

        if match:
            return json.loads(match.group())

    except Exception:
        pass

    return None


def evaluate_metric(metric_name, query, generated_output):

    system_prompt = "You are an evaluator agent."

    human_prompt = f"""
    Evaluate the output.

    Metric:
    {metric_name}

    Score from 1-10.

    Return STRICT JSON:

    {{
        "score": 8,
        "reason": "..."
    }}

    Query:
    {query}

    Output:
    {generated_output}
    """

    response = invoke_llm(
        system_prompt,
        human_prompt
    )

    parsed = extract_json(response)

    if parsed is None:

        parsed = {
            "score": 5,
            "reason": "Failed parsing"
        }

    return parsed


def evaluate_all_metrics(
    architecture_name,
    query,
    final_answer,
    decomposition=None,
    validation=None,
    reflection=None
):

    metrics = {}

    metrics["answer_depth"] = evaluate_metric(
        "Answer Depth Score",
        query,
        final_answer
    )

    metrics["answer_relevance"] = evaluate_metric(
        "Answer Relevance Score",
        query,
        final_answer
    )

    if decomposition:

        metrics["subquery_quality"] = evaluate_metric(
            "Subquery Quality Score",
            query,
            decomposition
        )

    if validation:

        metrics["source_relevance"] = evaluate_metric(
            "Source Relevance Score",
            query,
            validation
        )

    if reflection:

        metrics["reflection_score"] = evaluate_metric(
            "Reflection Score",
            query,
            reflection
        )

    metrics_path = os.path.join(
        DIRS["metrics"],
        f"{architecture_name}_metrics.json"
    )

    save_json(metrics_path, metrics)

    return metrics