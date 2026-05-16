
DECOMPOSER_TOOL = {
    "type": "function",
    "function": {
        "name": "decompose_plan",
        "description": "Decompose research plan into focused subqueries",
        "parameters": {
            "type": "object",
            "properties": {
                "subqueries": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "The decomposed subqueries"
                }
            },
            "required": ["subqueries"]
        }
    }
}


SOURCE_VALIDATION_TOOL = {
    "type": "function",
    "function": {
        "name": "validate_source",
        "description": "Validate the relevance and reliability of the sources for the research question in terms of whether it provides useful information to answer the research question",
        "parameters": {
            "type": "object",
            "properties": {
                "questions_with_scores": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_id": {
                                "type": "integer",
                                "description": "ID of the question"
                            },
                            "score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Relevance and reliability score from 1 to 10"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for the relevance and reliability score"
                            }
                        },
                        "required": ["score", "reason"]
                    }
                }
            },
            "required": ["questions_with_scores"]
        }
    }
}



REFLECTION_TOOL = {
    "type": "function",
    "function": {
        "name": "reflect_on_sources",
        "description": "Reflect on the validated sources and determine if more research is needed. Provide instructions for the next iteration if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "info_needed": {
                    "type": "boolean",
                    "description": "Whether more information is needed"
                },
                "instructions": {
                    "type": "string",
                    "description": "Instructions for the next iteration if more information is needed"
                }
            },
            "required": ["info_needed", "instructions"]
        }
    }
}