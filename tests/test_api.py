from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


class DummyPipeline:
    def chat(self, session_id: str, message: str):
        return {
            "answer": "stub",
            "sources": [{"source": "manual.txt", "page": None, "score": 0.9}],
            "cached": False,
            "tool_used": False,
            "tool_name": None,
            "latency_ms": 1.2,
        }

    def get_runtime_config(self):
        return {
            "app_name": "RAG Knowledge Assistant",
            "llm_provider": "local",
            "llm_model": "stub-model",
            "llm_mode": "local-fallback",
            "embedding_provider": "local",
            "embedding_model": "local-hash-256d",
            "embedding_mode": "local-fallback",
            "real_ai_ready": False,
            "has_openai_key": False,
            "top_k": 5,
            "temperature": 0.0,
            "chunk_size": 800,
            "chunk_overlap": 120,
            "cache_ttl": 3600,
        }

    def clear_memory(self, session_id: str) -> None:
        return None

    def ingest(self, force: bool = False):
        from app.rag.types import IngestionStats

        return IngestionStats(
            files=1,
            documents=1,
            chunks=1,
            embedding_model="local-hash-256d",
            vector_store_location="vector_store",
            elapsed_seconds=0.1,
            reused_index=False,
        )


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint(monkeypatch):
    monkeypatch.setattr("app.api.routes.get_rag_pipeline", lambda: DummyPipeline())
    client = TestClient(app)

    response = client.post("/chat", json={"session_id": "demo001", "message": "hello"})

    assert response.status_code == 200
    assert response.json()["answer"] == "stub"
    assert response.json()["cached"] is False
