from __future__ import annotations

import json
import logging
import pickle
from dataclasses import asdict
from pathlib import Path

import numpy as np

from app.rag.types import RetrievedDocument

logger = logging.getLogger(__name__)

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - environment dependent
    faiss = None


class FaissVectorStore:
    """FAISS-backed vector store with numpy fallback when FAISS is unavailable."""

    def __init__(self, store_path: Path, index_path: Path, manifest_path: Path) -> None:
        self.store_path = store_path
        self.index_path = index_path
        self.manifest_path = manifest_path
        self.texts: list[str] = []
        self.metadatas: list[dict[str, object]] = []
        self.vectors = np.empty((0, 0), dtype="float32")
        self._index = None

    def exists(self) -> bool:
        return self.store_path.exists() and self.manifest_path.exists()

    def save(
        self,
        texts: list[str],
        metadatas: list[dict[str, object]],
        vectors: np.ndarray,
        manifest: dict[str, object],
    ) -> None:
        normalized = self._normalize(vectors)
        self.texts = texts
        self.metadatas = metadatas
        self.vectors = normalized
        self._build_index(normalized)

        payload = {
            "texts": texts,
            "metadatas": metadatas,
            "vectors": normalized,
        }
        with self.store_path.open("wb") as file:
            pickle.dump(payload, file)
        with self.manifest_path.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, ensure_ascii=False, indent=2)

        if faiss is not None and self._index is not None:
            faiss.write_index(self._index, str(self.index_path))
        else:
            self.index_path.write_bytes(normalized.tobytes())

    def load(self) -> None:
        with self.store_path.open("rb") as file:
            payload = pickle.load(file)
        self.texts = payload["texts"]
        self.metadatas = payload["metadatas"]
        self.vectors = payload["vectors"]
        self._build_index(self.vectors)

    def load_manifest(self) -> dict[str, object] | None:
        if not self.manifest_path.exists():
            return None
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def search(self, query_vector: np.ndarray, top_k: int) -> list[RetrievedDocument]:
        if self.vectors.size == 0:
            return []
        vector = self._normalize(np.asarray([query_vector], dtype="float32"))[0]
        count = min(top_k, len(self.texts))
        if faiss is not None and self._index is not None:
            scores, indices = self._index.search(np.asarray([vector], dtype="float32"), count)
            pairs = zip(indices[0].tolist(), scores[0].tolist(), strict=False)
        else:
            scores_array = np.dot(self.vectors, vector)
            ranked_indices = np.argsort(scores_array)[::-1][:count]
            pairs = ((int(idx), float(scores_array[idx])) for idx in ranked_indices)
        results: list[RetrievedDocument] = []
        for pair in pairs:
            if faiss is not None and self._index is not None:
                idx, score = pair
            else:
                idx, score = pair
            if idx < 0:
                continue
            results.append(
                RetrievedDocument(
                    page_content=self.texts[idx],
                    metadata=self.metadatas[idx],
                    score=round(float(score), 4),
                )
            )
        return results

    def _build_index(self, vectors: np.ndarray) -> None:
        if faiss is None or vectors.size == 0:
            self._index = None
            return
        dimension = vectors.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)
        self._index = index

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        if vectors.size == 0:
            return vectors.astype("float32")
        array = vectors.astype("float32")
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return array / norms


def build_manifest(file_signatures: list[dict[str, object]], chunk_size: int, chunk_overlap: int, model_name: str) -> dict[str, object]:
    return {
        "files": file_signatures,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": model_name,
    }


def manifest_matches(current: dict[str, object], existing: dict[str, object] | None) -> bool:
    return existing == current
