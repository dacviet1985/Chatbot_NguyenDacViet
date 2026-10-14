# Kiến trúc hệ thống

## Offline ingestion flow

PDF/TXT
↓
Loader
↓
Chunking
↓
Embedding
↓
FAISS / numpy fallback
↓
Metadata

### Mô tả
- `app/rag/loader.py`: đọc PDF/TXT và chuẩn hóa metadata `source`, `page`, `document_id`.
- `app/rag/chunker.py`: chia văn bản theo `chunk_size` và `chunk_overlap`.
- `app/rag/embeddings.py`: hỗ trợ OpenAI embedding mặc định, HuggingFace tùy chọn, local hash fallback để demo/test khi chưa có API key.
- `app/rag/vector_store.py`: lưu vectors, metadata, manifest; ưu tiên FAISS, fallback sang numpy similarity nếu môi trường chưa có FAISS.

## Online serving flow

User
↓
Streamlit
↓
FastAPI
↓
Cache
↓
Memory
↓
Retriever
↓
Top-K
↓
Query Transformation
↓
Prompt
↓
LLM / local grounded answerer
↓
Answer + Citations
↓
Logging

## Tool integration

Tool hiện tại gồm:
- `calculator` trong `app/tools/calculator.py`
- `weather` trong `app/tools/weather.py`

Flow khi cần tool:
1. User hỏi phép tính.
2. Pipeline nhận diện biểu thức số học.
3. Calculator chạy trước RAG.
4. Kết quả trả về trực tiếp.
5. Log `[TOOL]` được ghi vào `logs/app.log`.

Flow khi cần weather tool:
1. User hỏi thời tiết theo địa điểm.
2. Pipeline nhận diện weather intent.
3. Tool gọi Open-Meteo geocoding + forecast API.
4. Kết quả trả về trực tiếp, không qua retrieval.
5. Source hiển thị `open-meteo.com`.

## Logging và monitoring

Mỗi request ghi:
- timestamp
- session_id
- query
- cache hit/miss
- retrieved documents
- tool
- latency
- final answer status

## Lý do chọn kiến trúc

- Đơn giản, dễ demo trên Windows.
- Không phụ thuộc quá nặng vào framework RAG.
- Có fallback local để unit test vẫn chạy khi không có OpenAI key.
- Có manifest để tránh ingest lại khi dữ liệu không đổi.
