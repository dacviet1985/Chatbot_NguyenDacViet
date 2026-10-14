from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="RAG Knowledge Assistant", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    huggingface_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="HUGGINGFACE_MODEL")
    allow_local_fallback: bool = Field(default=True, alias="ALLOW_LOCAL_FALLBACK")
    request_timeout: float = Field(default=30.0, alias="REQUEST_TIMEOUT")

    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=5, alias="TOP_K")
    score_threshold: float = Field(default=0.2, alias="SCORE_THRESHOLD")
    temperature: float = Field(default=0.0, alias="TEMPERATURE")
    memory_window: int = Field(default=6, alias="MEMORY_WINDOW")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    use_query_transformation: bool = Field(default=True, alias="USE_QUERY_TRANSFORMATION")
    use_reranker: bool = Field(default=False, alias="USE_RERANKER")

    knowledge_dir: Path = Field(default=ROOT_DIR / "Knowledge", alias="KNOWLEDGE_DIR")
    vector_store_dir: Path = Field(default=ROOT_DIR / "vector_store", alias="VECTOR_STORE_DIR")
    logs_dir: Path = Field(default=ROOT_DIR / "logs", alias="LOGS_DIR")
    evaluation_dir: Path = Field(default=ROOT_DIR / "evaluation", alias="EVALUATION_DIR")

    cache_namespace: str = Field(default="rag-chatbot", alias="CACHE_NAMESPACE")

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def llm_mode(self) -> str:
        if self.llm_provider.lower() == "openai" and self.has_openai_key:
            return "openai"
        return "local-fallback"

    @property
    def embedding_mode(self) -> str:
        if self.embedding_provider.lower() == "openai" and self.has_openai_key:
            return "openai"
        if self.embedding_provider.lower() in {"huggingface", "hf"}:
            return "huggingface"
        return "local-fallback"

    @property
    def real_ai_ready(self) -> bool:
        return self.llm_mode == "openai" and self.embedding_mode == "openai"

    @property
    def log_file(self) -> Path:
        return self.logs_dir / "app.log"

    @property
    def index_path(self) -> Path:
        return self.vector_store_dir / "index.bin"

    @property
    def store_payload_path(self) -> Path:
        return self.vector_store_dir / "store.pkl"

    @property
    def manifest_path(self) -> Path:
        return self.vector_store_dir / "manifest.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.knowledge_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.evaluation_dir.mkdir(parents=True, exist_ok=True)
    return settings
