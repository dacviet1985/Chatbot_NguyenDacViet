from __future__ import annotations

import logging

from app.core.config import Settings
from app.rag.embeddings import BaseEmbedder
from app.rag.types import RetrievedDocument
from app.rag.vector_store import FaissVectorStore
from app.utils.text import keyword_overlap_score, normalize_text

logger = logging.getLogger(__name__)

_FOLLOW_UP_MARKERS = (
    "còn",
    "thế còn",
    "vậy còn",
    "nếu vậy",
    "trường hợp đó",
    "cái đó",
    "điều đó",
    "họ thì sao",
)


class Retriever:
    """Retrieves top-k relevant chunks from the vector store."""

    def __init__(self, vector_store: FaissVectorStore, embedder: BaseEmbedder, settings: Settings) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.settings = settings

    def transform_query(self, query: str, history: list[dict[str, str]]) -> str:
        normalized = normalize_text(query)
        if not self.settings.use_query_transformation or not history:
            return query
        if any(normalized.startswith(marker) for marker in _FOLLOW_UP_MARKERS) or len(normalized.split()) <= 6:
            prior_questions = [item["content"] for item in history if item["role"] == "user"]
            if prior_questions:
                return f"{prior_questions[-1]} | follow-up: {query}"
        return query

    def retrieve(self, query: str, history: list[dict[str, str]] | None = None) -> tuple[str, list[RetrievedDocument]]:
        transformed_query = self.transform_query(query, history or [])
        query_vector = self.embedder.embed_query(transformed_query)
        results = self.vector_store.search(query_vector, self.settings.top_k)
        filtered: list[RetrievedDocument] = []
        for item in results:
            lexical_score = keyword_overlap_score(transformed_query, item.page_content)
            item.metadata["lexical_score"] = round(lexical_score, 4)
            if item.score < self.settings.score_threshold:
                continue
            if lexical_score < 0.2:
                continue
            filtered.append(item)
        filtered.sort(key=lambda item: (item.score + float(item.metadata.get("lexical_score", 0.0))), reverse=True)
        logger.info("[RETRIEVER] Query: %s | Top K: %s", transformed_query, self.settings.top_k)
        for index, item in enumerate(filtered, start=1):
            logger.info(
                "[RETRIEVER] %s. %s - page %s - score=%s - lexical=%s",
                index,
                item.metadata.get("source"),
                item.metadata.get("page"),
                item.score,
                item.metadata.get("lexical_score"),
            )
        return transformed_query, filtered
