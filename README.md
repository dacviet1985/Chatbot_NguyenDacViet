# END-TO-END RAG CHATBOT

## 1. Giới thiệu project

Project xây dựng trợ lý hỏi – đáp trên dữ liệu tùy chọn PDF/TXT theo kiến trúc RAG end-to-end.

Tính năng chính:
- Ingest tài liệu PDF/TXT từ `Knowledge/`
- Chunking + metadata
- Embedding cấu hình qua `.env`
- Lưu vector vào FAISS, có numpy fallback khi môi trường chưa hỗ trợ FAISS
- Retrieval Top-K
- Prompt grounding chống hallucination
- Citation/source bắt buộc
- Conversation memory
- Calculator tool
- Weather tool
- FastAPI backend
- Streamlit UI
- TTL cache
- Logging ra `logs/app.log`
- Evaluation 12 câu hỏi
- Failure cases

## 2. Kiến trúc

Xem chi tiết tại [docs/architecture.md](docs/architecture.md).

## 3. Công nghệ

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- Streamlit
- OpenAI API
- FAISS hoặc numpy fallback
- PyPDF
- Pytest

## 4. Cấu trúc thư mục

- [app](app)
- [ui](ui)
- [scripts](scripts)
- [Knowledge](Knowledge)
- [evaluation](evaluation)
- [docs](docs)
- [tests](tests)

## 5. Cài đặt

### Tạo môi trường ảo

- `python -m venv .venv`
- `.venv\Scripts\activate`

### Cài dependencies

- `pip install -r requirements.txt`

## 6. Cấu hình `.env`

Sao chép `.env.example` thành `.env` và cập nhật nếu cần.

Project hiện đã có sẵn file [/.env](.env) nội bộ trong máy để bạn bật AI thật nhanh hơn.

Biến quan trọng:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `TOP_K`
- `CACHE_TTL`
- `USE_QUERY_TRANSFORMATION`

Nếu chưa có `OPENAI_API_KEY`, hệ thống vẫn chạy bằng local embedding + local grounded answerer để test/demo cơ bản.

### Bật AI thật bằng OpenAI

1. Mở [/.env](.env)
2. Dán `OPENAI_API_KEY` của bạn
3. Giữ:
  - `LLM_PROVIDER=openai`
  - `EMBEDDING_PROVIDER=openai`
4. Chạy kiểm tra kết nối:
  - `python scripts/check_openai_setup.py`
5. Rebuild lại vector store bằng embedding thật:
  - `python scripts/ingest.py`
6. Chạy API/UI lại:
  - `uvicorn app.main:app --reload`
  - `streamlit run ui/streamlit_app.py`

Lưu ý quan trọng:
- Nếu trước đó bạn đã ingest bằng local fallback, bạn phải chạy lại ingest sau khi thêm key.
- Sidebar của Streamlit sẽ hiển thị `Real AI: READY` khi OpenAI đã sẵn sàng.

## 7. Tạo sample data

Chạy:
- `python scripts/generate_sample_data.py`

## 8. Ingest dữ liệu

Chạy:
- `python scripts/ingest.py`

Output gồm:
- số file
- số documents
- số chunks
- embedding model
- vector store location
- thời gian ingest

## 9. Chạy FastAPI

Chạy:
- `uvicorn app.main:app --reload`

API chính:
- `GET /health`
- `GET /config`
- `POST /chat`
- `POST /admin/rebuild`
- `POST /memory/{session_id}/clear`

## 10. Chạy Streamlit

Chạy:
- `streamlit run ui/streamlit_app.py`

UI hỗ trợ:
- chat
- clear conversation
- rebuild index
- upload PDF/TXT vào `Knowledge/`
- hiển thị source, cache, latency, tool

## 11. API examples

### `GET /health`

Response:

```json
{"status":"ok"}
```

### `POST /chat`

Request:

```json
{
  "session_id": "demo001",
  "message": "Chính sách nghỉ phép năm là gì?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "sample_01.pdf",
      "page": 1,
      "score": 0.89
    }
  ],
  "cached": false,
  "tool_used": false,
  "latency_ms": 123.45
}
```

## 12. RAG flow

`Query -> Retriever -> Top-K documents -> Prompt -> LLM -> Answer`

Chi tiết:
1. Normalize query
2. Cache check
3. Tool check
4. Query transformation nếu là follow-up
5. Embed query
6. Similarity search
7. Build context + prompt
8. LLM hoặc local grounded answerer
9. Return answer + citations

## 13. Memory

- Lưu theo `session_id`
- Giới hạn số message bằng `MEMORY_WINDOW`
- Có thể reset qua API và Streamlit

## 14. Tool

Tool hiện tại:
- `calculator`
- `weather`

Ví dụ:
- `184 * 12 * 5`
- `Tính 100 + 20 * 3`
- `thời tiết Hà Nội hôm nay`
- `nhiệt độ ở Đà Nẵng bây giờ`

## 15. Cache

- TTL cache in-memory
- Log `[CACHE] HIT/MISS`
- Response có `cached=true/false`

## 16. Evaluation

File câu hỏi:
- [evaluation/test_questions.json](evaluation/test_questions.json)

Chạy:
- `python scripts/evaluate.py`

Kết quả:
- [evaluation/evaluation_results.csv](evaluation/evaluation_results.csv)

Metrics:
- Faithfulness: 0 hoặc 1
- Relevance: 0-2
- Average latency
- Cache hit rate

## 17. Failure cases

Xem tại [evaluation/failure_cases.md](evaluation/failure_cases.md).

## 18. Bonus RAG

Bonus đã triển khai:
- Query transformation cho follow-up question

Config:
- `USE_QUERY_TRANSFORMATION=true`

## 19. Testing

Chạy:
- `pytest`

Test bao phủ:
- document loading
- chunking
- metadata
- retriever
- cache
- API `/health`
- API `/chat`

## 20. Troubleshooting

### Thiếu `OPENAI_API_KEY`
- Hệ thống fallback sang local answerer.
- Unit test vẫn chạy được.

### Muốn dùng AI thật nhưng vẫn thấy local fallback
- Kiểm tra sidebar `LLM mode` và `Embedding mode` trên UI.
- Chạy `python scripts/check_openai_setup.py`.
- Chạy lại `python scripts/ingest.py` sau khi key hợp lệ.

### Knowledge folder rỗng
- Thêm file vào `Knowledge/` rồi chạy lại ingest.

### FAISS không cài được trên Windows/Python build hiện tại
- Hệ thống tự fallback sang numpy similarity.
- Vẫn giữ cùng interface vector store.

### PDF lỗi
- Loader log exception và bỏ qua file lỗi.

### API timeout hoặc OpenAI error
- Pipeline fallback sang local grounded answerer nếu có context.

## 21. Tài liệu bổ sung

- [docs/architecture.md](docs/architecture.md)
- [docs/demo_script.md](docs/demo_script.md)
- [docs/report.md](docs/report.md)
- [docs/rag_explanation.md](docs/rag_explanation.md)
- [docs/project_checklist.md](docs/project_checklist.md)
