
# ============================================================
# CONTEXT RELEVANCE
# ============================================================

CONTEXT_SYSTEM_PROMPT = """
You are an expert evaluator.

Evaluate how useful and relevant the retrieved context is
for answering the user question.

Evaluate:
- relevance
- usefulness
- coverage
- noise

STRICTLY use the tool.
Return:
- score (0-10)
- short reason
"""

CONTEXT_USER_PROMPT = """
Architecture:
{architecture}

User Question:
{query}

Sub Questions:
{subqueries}

Collected Sources:
{sources}

Validated Sources:
{validated_sources}

Final Answer:
{final_answer}
"""



# ============================================================
# ANSWER RELEVANCE
# ============================================================

ANSWER_SYSTEM_PROMPT = """
You are an expert evaluator.

Evaluate whether the final answer actually answers
the user question.

Evaluate:
- completeness
- correctness
- focus
- missing aspects

STRICTLY use the tool.
Return:
- score (0-10)
- short reason
"""

ANSWER_USER_PROMPT = """
Architecture:
{architecture}

User Question:
{query}

Final Answer:
{final_answer}
"""


# ============================================================
# FAITHFULNESS / GROUNDEDNESS
# ============================================================

FAITHFULNESS_SYSTEM_PROMPT = """
You are an expert evaluator.

Evaluate whether the claims in the final answer
are supported by the retrieved evidence/context.

Evaluate:
- groundedness
- hallucinations
- unsupported claims
- evidence support

STRICTLY use the tool.
Return:
- score (0-10)
- short reason
"""

FAITHFULNESS_USER_PROMPT = """
Architecture:
{architecture}

User Question:
{query}

Collected Sources:
{sources}

Validated Sources:
{validated_sources}

Final Answer:
{final_answer}
"""


# ============================================================
# DECOMPOSITION QUALITY
# ============================================================

DECOMPOSITION_SYSTEM_PROMPT = """
You are an expert evaluator.

Evaluate the decomposition quality.

Evaluate:
- coverage of subquestions
- redundancy
- granularity
- logical structure
- dependency quality

If decomposition does not exist,
give score 0.

STRICTLY use the tool.
Return:
- score (0-10)
- short reason
"""

DECOMPOSITION_USER_PROMPT = """
Architecture:
{architecture}

User Question:
{query}

Sub Questions:
{subqueries}

Plan:
{plan}
"""


# ============================================================
# REFLECTION QUALITY
# ============================================================

REFLECTION_SYSTEM_PROMPT = """
You are an expert evaluator.

Evaluate whether reflection/self-correction
improved the reasoning pipeline.

Evaluate:
- error correction
- iterative improvement
- retrieval refinement
- answer improvement

If reflection does not exist,
give score 0.

STRICTLY use the tool.
Return:
- score (0-10)
- short reason
"""

REFLECTION_USER_PROMPT = """
Architecture:
{architecture}

User Question:
{query}

Reflection:
{reflection}

Iterations:
{loop_count}

Validated Sources:
{validated_sources}

Final Answer:
{final_answer}
"""