from src.backend.architectures.single_llm_call import app as single_llm_call
from src.backend.architectures.single_search_llm import app as single_search_llm
from src.backend.architectures.iterative_search_llm import app as iterative_search_llm
from src.backend.architectures.decomposer_search_synthesis import app as decomposer_search_synthesis

ARCHITECTURES = {
    "single_llm_call": single_llm_call,
    "single_search_llm": single_search_llm,
    "iterative_search_llm": iterative_search_llm,
    "decomposer_search_synthesis": decomposer_search_synthesis,
}