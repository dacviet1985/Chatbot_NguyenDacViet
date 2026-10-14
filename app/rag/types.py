from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RAGDocument:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievedDocument:
    page_content: str
    metadata: dict[str, Any]
    score: float


@dataclass(slots=True)
class IngestionStats:
    files: int
    documents: int
    chunks: int
    embedding_model: str
    vector_store_location: str
    elapsed_seconds: float
    reused_index: bool
