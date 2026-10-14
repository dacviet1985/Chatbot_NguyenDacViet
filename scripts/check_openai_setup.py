from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.rag.embeddings import EmbeddingFactory


if __name__ == "__main__":
    settings = get_settings()
    if not settings.has_openai_key:
        print("OPENAI_API_KEY đang trống trong .env")
        print("Hãy dán API key vào file .env rồi chạy lại script này.")
        raise SystemExit(1)

    print("=== OPENAI SETUP CHECK ===")
    print(f"LLM provider: {settings.llm_provider}")
    print(f"LLM model: {settings.openai_model}")
    print(f"Embedding provider: {settings.embedding_provider}")
    print(f"Embedding model: {settings.embedding_model}")

    try:
        embedder = EmbeddingFactory.create(settings)
        vector = embedder.embed_query("Xin chào, đây là kiểm tra OpenAI embedding.")
        print(f"Embedding OK | dim={len(vector)}")
    except Exception as exc:
        print(f"Embedding FAILED: {exc}")
        raise SystemExit(1) from exc

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý kiểm tra kết nối."},
                {"role": "user", "content": "Hãy trả lời đúng 3 từ: ket noi thanh cong"},
            ],
        )
        answer = (response.choices[0].message.content or "").strip()
        print(f"LLM OK | response={answer}")
    except Exception as exc:
        print(f"LLM FAILED: {exc}")
        raise SystemExit(1) from exc

    print("OpenAI đã sẵn sàng. Hãy chạy lại python scripts/ingest.py để rebuild vector store bằng embedding thật.")
