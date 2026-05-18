from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "ollama"  # 'openai' or 'ollama'
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    # ollama_model: str = "llama3.1:8b"
    ollama_model: str = "qwen3:8b"

    # Logging
    log_level: str = "INFO"

    # Paths
    dataset_cache_dir: str = "./data/cache"
    vector_store_path: str = "./data/vectorstore"
    evaluation_output_dir: str = "./data/evaluation"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()