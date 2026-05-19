
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
        "name": "validate_source",
        "description": "Validate the relevance and reliability of the sources for the research question in terms of whether it provides useful information to answer the research question",
        "parameters": {
            "type": "object",
            "properties": {
                "source_evaluations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "integer",
                                "description": "ID of the source"
                            },
                            "score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Relevance and reliability score of the source to question from 1 to "
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for the relevance and reliability score"
                            },
                            "claims": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Claims which can be claimed using the sources"
                            }
                        },
                        "required": ["source_id", "score", "reason", "claims"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["questions_with_scores"],
            "additionalProperties": False
        }
    }
}



REFLECTION_TOOL = {
    "type": "function",
    "function": {
        "name": "reflect_on_sources",
        "description": "Reflect on the validated sources and determine if more research is needed. Provide instructions to generate new sub-questions for the next iteration if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "info_needed": {
                    "type": "boolean",
                    "description": "Whether more information is needed"
                },
                "instructions": {
                    "type": "string",
                    "description": "Instructions to generate new sub-questions for the next iteration if more information is needed"
                }
            },
            "required": ["info_needed", "instructions"],
            "additionalProperties": False
        }
    }
}