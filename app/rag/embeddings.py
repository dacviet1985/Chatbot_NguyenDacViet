from __future__ import annotations

import hashlib
import importlib
import logging
from abc import ABC, abstractmethod

import numpy as np

from app.core.config import Settings
from app.utils.text import tokenize

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    model_name: str

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        raise NotImplementedError


class LocalHashEmbedder(BaseEmbedder):
    """Deterministic local embedder for testing and offline demo fallback."""

    def __init__(self, dimensions: int = 512) -> None:
        self.dimensions = dimensions
        self.model_name = f"local-hash-{dimensions}d"

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self.embed_query(text) for text in texts]).astype("float32")

    def embed_query(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype="float32")
        tokens = tokenize(text)
        if not tokens:
            return vector
        features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        for token in features:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.astype("float32")


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model_name: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        response = self.client.embeddings.create(model=self.model_name, input=texts)
        return np.array([item.embedding for item in response.data], dtype="float32")

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_texts([text])[0]


class HuggingFaceEmbedder(BaseEmbedder):
    def __init__(self, model_name: str) -> None:
        try:
            sentence_transformers = importlib.import_module("sentence_transformers")
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers chưa được cài. Hãy cài thêm để dùng HuggingFace embedding."
            ) from exc
        SentenceTransformer = sentence_transformers.SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype="float32")

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(self.model.encode([text], normalize_embeddings=True)[0], dtype="float32")


class EmbeddingFactory:
    """Creates the configured embedding provider with safe fallback."""

    @staticmethod
    def create(settings: Settings) -> BaseEmbedder:
        provider = settings.embedding_provider.lower().strip()
        if provider == "openai":
            if settings.openai_api_key:
                logger.info("Using OpenAI embeddings: %s", settings.embedding_model)
                return OpenAIEmbedder(settings.openai_api_key, settings.embedding_model)
            if not settings.allow_local_fallback:
                raise RuntimeError("Thiếu OPENAI_API_KEY cho embedding provider=openai.")
            logger.warning("Thiếu OPENAI_API_KEY. Chuyển sang local hash embedding fallback.")
            return LocalHashEmbedder()
        if provider in {"huggingface", "hf", "local"}:
            if provider == "local":
                return LocalHashEmbedder()
            return HuggingFaceEmbedder(settings.huggingface_model)
        raise RuntimeError(f"Embedding provider không hỗ trợ: {settings.embedding_provider}")
