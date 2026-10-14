from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SourceItem(BaseModel):
    source: str
    page: int | None = None
    score: float | None = None


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message must not be empty")
        return cleaned


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)
    cached: bool = False
    tool_used: bool = False
    tool_name: str | None = None
    latency_ms: float


class HealthResponse(BaseModel):
    status: str = "ok"


class IngestResponse(BaseModel):
    files: int
    documents: int
    chunks: int
    embedding_model: str
    vector_store_location: str
    elapsed_seconds: float
    reused_index: bool


class ConfigResponse(BaseModel):
    app_name: str
    llm_provider: str
    llm_model: str
    llm_mode: str
    embedding_provider: str
    embedding_model: str
    embedding_mode: str
    real_ai_ready: bool
    has_openai_key: bool
    top_k: int
    temperature: float
    chunk_size: int
    chunk_overlap: int
    cache_ttl: int


class ClearMemoryResponse(BaseModel):
    status: str
    session_id: str
