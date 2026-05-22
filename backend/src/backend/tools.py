
PRE_PLANNER_TOOL = {   
    "type": "function",
    "function": {
        "name": "pre_plan",
        "description": "Pre-plan the research approach",
        "parameters": {
            "type": "object",
            "properties": {
                "research_required": {
                    "type": "boolean",
                    "description": "Indicates if research is required"
                },
                "reasoning_depth": {
                    "type": "enum",
                    "enum": ["shallow", "medium", "deep"],
                    "description": "The depth of reasoning needed (shallow, medium, deep) if research is required."
                },
                "tools_needed": {
                    "type": "array",
                    "items": {
                        "type": "enum",
                        "enum": ["web_search", "arxiv", "wikipedia"],
                    },
                    "description": "The tools needed if research is required. web_search for general questions, arxiv for scientific research questions, wikipedia for factual questions."
                }
            },
            "required": ["research_required"],
            "additionalProperties": False
        }
    }
}


# DECOMPOSER_TOOL = {
#     "type": "function",
#     "function": {
#         "name": "decompose_plan",
#         "description": "Decompose research plan into focused subqueries",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "subqueries": {
#                     "type": "array",
#                     "items": {
#                         "type": "string"
#                     },
#                     "description": "The decomposed subqueries"
#                 }
#             },
#             "required": ["subqueries"]
#         }
#     }
# }
DECOMPOSER_TOOL = {
    "type": "function",
    "function": {
        "name": "decompose_plan",
        "description": "Decompose research plan into focused subqueries for each tool",
        "parameters": {
            "type": "object",
            "properties": {
                "web_search": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "description": "Subqueries for the web_search tool"
                },
                "arxiv": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "description": "Subqueries for the arxiv tool"
                },
                "wikipedia": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "description": "Subqueries for the wikipedia tool"
                }
            },
            "required": ["web_search", "arxiv", "wikipedia"],
            "additionalProperties": False
        }
    }
}
DECOMPOSER_TOOL_ITER_2 = {
    "type": "function",
    "function": {
        "name": "decompose_plan",
        "description": "Decompose research plan into focused subqueries using instructions from reflection",
        "parameters": {
            "type": "object",
            "properties": {
                "web_search": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "description": "Subqueries for the web_search tool"
                },
                "arxiv": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "description": "Subqueries for the arxiv tool"
                },
                "wikipedia": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "description": "Subqueries for the wikipedia tool"
                }
            },
            "required": ["web_search", "arxiv", "wikipedia"],
            "additionalProperties": False
        }
    }
}

SOURCE_VALIDATION_TOOL = {
    "type": "function",
    "function": {
        "name": "validate_source_claims",
        "description": (
            "Extract claims supported by the provided sources and assign "
            "a confidence score for how strongly each source supports "
            "the claim with respect to the research question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "claims": {
                    "type": "array",
                    "description": (
                        "List of claims inferred from the sources. "
                        "A source can produce multiple claims or none."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": (
                                    "A factual claim supported by the source"
                                )
                            },
                            "confidence_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": (
                                    "Confidence score indicating how strongly "
                                    "the source supports the claim in relation "
                                    "to the research question"
                                )
                            },
                            "source_id": {
                                "type": "integer",
                                "description": "ID of the source supporting the claim"
                            },
                            "justification": {
                                "type": "string",
                                "description": (
                                    "Short explanation of why the source "
                                    "supports the claim"
                                )
                            }
                        },
                        "required": [
                            "claim",
                            "confidence_score",
                            "source_id",
                            "justification"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["claims"],
            "additionalProperties": False
        }
    }
}

SOURCE_VALIDATION_TOOL_ITER2 = {
    "type": "function",
    "function": {
        "name": "validate_source_claims",
        "description": (
            "Extract claims supported by the provided sources and assign "
            "a confidence score for how strongly each source supports "
            "the claim with respect to the research question. "
            "Use the additional instructions to generate claims."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "claims": {
                    "type": "array",
                    "description": (
                        "List of claims inferred from the sources. "
                        "A source can produce multiple claims or none."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {
                                "type": "string",
                                "description": (
                                    "A factual claim supported by the source"
                                )
                            },
                            "confidence_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": (
                                    "Confidence score indicating how strongly "
                                    "the source supports the claim in relation "
                                    "to the research question"
                                )
                            },
                            "source_id": {
                                "type": "integer",
                                "description": "ID of the source supporting the claim"
                            },
                            "justification": {
                                "type": "string",
                                "description": (
                                    "Short explanation of why the source "
                                    "supports the claim"
                                )
                            }
                        },
                        "required": [
                            "claim",
                            "confidence_score",
                            "source_id",
                            "justification"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["claims"],
            "additionalProperties": False
        }
    }
}



# REFLECTION_TOOL = {
#     "type": "function",
#     "function": {
#         "name": "reflect_on_sources",
#         "description": "Reflect on the validated sources and determine if more research is needed. Provide instructions to generate new sub-questions for the next iteration if needed.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "info_needed": {
#                     "type": "boolean",
#                     "description": "Whether more information is needed"
#                 },
#                 "instructions": {
#                     "type": "string",
#                     "description": "Instructions to generate new sub-questions for the next iteration if more information is needed"
#                 }
#             },
#             "required": ["info_needed", "instructions"],
#             "additionalProperties": False
#         }
#     }
# }

REFLECTION_TOOL = {
    "type": "function",
    "function": {
        "name": "reflect_on_claims",
        "description": "Determine the next workflow node based on validated claims.",
        "parameters": {
            "type": "object",
            "properties": {
                "next_node": {
                    "type": "string",
                    "enum": [
                        "validation_node",
                        "decomposer_node"
                    ]
                },
                "reasoning": {
                    "type": "string"
                },
                "instructions": {
                    "type": "string"
                }
            },
            "required": [
                "next_node",
                "reasoning",
                "instructions"
            ]
        }
    }
}