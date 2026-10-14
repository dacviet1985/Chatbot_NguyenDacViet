from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.logging_config import setup_logging
from app.rag.pipeline import get_rag_pipeline


if __name__ == "__main__":
    setup_logging()
    pipeline = get_rag_pipeline()
    stats = pipeline.ingest(force=False)
    print("=== INGESTION SUMMARY ===")
    print(f"Files: {stats.files}")
    print(f"Documents: {stats.documents}")
    print(f"Chunks: {stats.chunks}")
    print(f"Embedding model: {stats.embedding_model}")
    print(f"Vector store: {stats.vector_store_location}")
    print(f"Reused index: {stats.reused_index}")
    print(f"Elapsed seconds: {stats.elapsed_seconds}")
