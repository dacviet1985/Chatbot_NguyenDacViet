from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.rag.embeddings import LocalHashEmbedder
from app.rag.retriever import Retriever
from app.rag.vector_store import FaissVectorStore


def test_retriever_returns_relevant_chunks(tmp_path):
    settings = Settings(
        EMBEDDING_PROVIDER="local",
        KNOWLEDGE_DIR=tmp_path / "Knowledge",
        VECTOR_STORE_DIR=tmp_path / "vector_store",
        LOGS_DIR=tmp_path / "logs",
        EVALUATION_DIR=tmp_path / "evaluation",
        TOP_K=2,
        SCORE_THRESHOLD=0.0,
    )
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    embedder = LocalHashEmbedder()
    store = FaissVectorStore(settings.store_payload_path, settings.index_path, settings.manifest_path)
    texts = [
        "Nhân viên chính thức có 12 ngày nghỉ phép năm hưởng lương.",
        "Thiết bị hỏng phải báo IT trong vòng 30 phút.",
    ]
    metadatas = [
        {"source": "sample_01.pdf", "page": 1, "chunk_id": "c1", "document_id": "d1"},
        {"source": "sample_02.pdf", "page": 2, "chunk_id": "c2", "document_id": "d2"},
    ]
    vectors = embedder.embed_texts(texts)
    store.save(texts, metadatas, vectors, {"files": [], "chunk_size": 800, "chunk_overlap": 120, "embedding_model": embedder.model_name})
    retriever = Retriever(store, embedder, settings)

    _, results = retriever.retrieve("nghỉ phép năm")

    assert results
    assert results[0].metadata["source"] == "sample_01.pdf"
