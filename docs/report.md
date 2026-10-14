# BÁO CÁO PROJECT END-TO-END RAG CHATBOT

## 1. Giới thiệu

Project xây dựng một hệ thống hỏi – đáp trên dữ liệu tùy chọn theo kiến trúc RAG end-to-end. Người dùng đưa tài liệu PDF/TXT vào thư mục `Knowledge/`, hệ thống ingest tài liệu, chunking, embedding, lưu vector vào vector store, sau đó trả lời câu hỏi qua FastAPI hoặc Streamlit UI.

Mục tiêu của project là xây dựng một trợ lý có khả năng:
- trả lời dựa trên dữ liệu nội bộ,
- có citation/source rõ ràng,
- có memory hội thoại,
- có cache,
- có ít nhất một tool,
- có evaluation và failure cases.

Ngoài RAG cơ bản, project hiện hỗ trợ 2 tool:
- `calculator`: dùng cho phép tính.
- `weather`: dùng cho truy vấn thời tiết realtime.

## 2. Kiến trúc hệ thống

### 2.1 Luồng offline ingestion

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

Các thành phần chính:
- [app/rag/loader.py](app/rag/loader.py): đọc PDF/TXT và tạo metadata `source`, `page`, `document_id`.
- [app/rag/chunker.py](app/rag/chunker.py): chia chunk theo `chunk_size` và `chunk_overlap`.
- [app/rag/embeddings.py](app/rag/embeddings.py): hỗ trợ OpenAI embedding mặc định, HuggingFace tùy chọn, local fallback để test.
- [app/rag/vector_store.py](app/rag/vector_store.py): lưu vectors, metadata, manifest và similarity search.

### 2.2 Luồng online serving

User  
↓  
Streamlit / API Client  
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
OpenAI LLM / local fallback  
↓  
Answer + Citations  
↓  
Logging  

Nếu query phù hợp với tool, pipeline sẽ rẽ nhánh sang tool thay vì RAG retrieval.

## 3. Prompt template và chống hallucination

Prompt nằm ở [app/rag/prompt.py](app/rag/prompt.py).

Nguyên tắc thiết kế:
1. Chỉ dùng thông tin trong `CONTEXT`.
2. Nếu không đủ context thì trả lời câu từ chối cố định.
3. Không tạo citation giả.
4. Trả lời trực tiếp bằng tiếng Việt.

Refusal text chuẩn:

> Xin lỗi, tôi không tìm thấy thông tin phù hợp trong tài liệu được cung cấp.

Nhờ đó hệ thống không được phép dùng kiến thức ngoài tài liệu nội bộ cho các câu hỏi RAG. Ví dụ câu hỏi về bảo hiểm thú cưng sẽ bị từ chối vì không có trong Knowledge Base.

## 4. Retrieval, citation và memory

### 4.1 Retrieval

Retriever được cài tại [app/rag/retriever.py](app/rag/retriever.py).

Các bước chính:
- normalize query,
- query transformation cho follow-up,
- embedding query,
- similarity search top-k,
- lexical filtering để giảm noise.

Metadata trả về gồm:
- `source`
- `page`
- `score`

### 4.2 Citation

Citation là bắt buộc. Mọi response grounded đều trả về trường `sources` trong API và hiển thị rõ trên Streamlit UI.

Ví dụ citation:
- `sample_01.pdf`, page 1
- `sample_03.txt`

### 4.3 Memory

Conversation memory được cài trong [app/rag/memory.py](app/rag/memory.py). Bộ nhớ lưu theo `session_id`, giới hạn bằng `MEMORY_WINDOW` và có thể reset qua API hoặc UI.

Ví dụ chứng minh memory:
- User: `Chính sách nghỉ phép năm là gì?`
- User: `Còn nhân viên thử việc thì sao?`

Hệ thống hiểu được follow-up question nhờ memory kết hợp query transformation.

## 5. Tool calling

### 5.1 Calculator tool

File: [app/tools/calculator.py](app/tools/calculator.py)

Ví dụ:
- `184 * 12 * 5`
- `Tính 100 + 20 * 3`

Tool chạy trước RAG và ghi log riêng.

### 5.2 Weather tool

File: [app/tools/weather.py](app/tools/weather.py)

Weather tool dùng Open-Meteo geocoding API và forecast API để lấy thời tiết realtime.

Ví dụ:
- `thời tiết Hà Nội hôm nay`
- `nhiệt độ ở Đà Nẵng bây giờ`

Kết quả trả về gồm:
- mô tả thời tiết,
- nhiệt độ hiện tại,
- độ ẩm,
- gió,
- min/max trong ngày,
- xác suất mưa.

Source hiển thị là `open-meteo.com`.

## 6. Cache và logging

### 6.1 Cache

Cache TTL in-memory nằm ở [app/core/cache.py](app/core/cache.py).

Flow cache:
- normalize query,
- kiểm tra cache,
- hit: trả kết quả ngay,
- miss: chạy tool hoặc RAG rồi lưu lại.

Response trả về có trường `cached=true/false`.

### 6.2 Logging

Logging cấu hình trong [app/core/logging_config.py](app/core/logging_config.py), ghi ra [logs/app.log](logs/app.log).

Các thông tin được log:
- timestamp,
- session_id,
- query,
- cache hit/miss,
- retrieved documents,
- tool call,
- latency,
- final answer.

## 7. Evaluation sheet

Evaluation question set nằm ở [evaluation/test_questions.json](evaluation/test_questions.json).

Script đánh giá nằm ở [scripts/evaluate.py](scripts/evaluate.py), kết quả ghi ra [evaluation/evaluation_results.csv](evaluation/evaluation_results.csv).

Metrics:
- Faithfulness: $0$ hoặc $1$
- Relevance: $0$ đến $2$
- Average latency
- Cache hit rate

Kết quả gần nhất:
- Total questions: 12
- Faithfulness rate: 1.0
- Average relevance: 1.917

## 8. Failure cases

Failure cases được mô tả trong [evaluation/failure_cases.md](evaluation/failure_cases.md).

### Failure case 1
- Question: `Công ty có hỗ trợ bảo hiểm cho thú cưng không?`
- Expected: từ chối trả lời vì không có dữ liệu liên quan.

### Failure case 2
- Question: `Laptop bị treo vào cuối ngày thì có được mang về nhà sửa không?`
- Expected: không hallucinate, chỉ nói phần nào được tài liệu hỗ trợ.

## 9. Hướng dẫn chạy

1. Tạo môi trường ảo  
   `python -m venv .venv`

2. Kích hoạt  
   `.venv\Scripts\activate`

3. Cài thư viện  
   `pip install -r requirements.txt`

4. Cấu hình [/.env](.env) và điền `OPENAI_API_KEY`

5. Ingest dữ liệu  
   `python scripts/ingest.py`

6. Chạy backend  
   `uvicorn app.main:app --reload`

7. Chạy UI  
   `streamlit run ui/streamlit_app.py`

8. Chạy test  
   `pytest`

## 10. Kết luận

Project đã đáp ứng 4 hạng mục nộp bài:
1. **Mã nguồn**: có cấu trúc thư mục rõ ràng, backend, UI, scripts, tests, `requirements.txt`.
2. **Dữ liệu**: có tài liệu mẫu PDF/TXT và script ingest vào vector store.
3. **Báo cáo**: có tài liệu kiến trúc, prompt, evaluation sheet, failure cases và hướng dẫn chạy.
4. **Demo**: có kịch bản demo trong [docs/demo_script.md](docs/demo_script.md), hỗ trợ memory, citation, cache, calculator tool và weather tool.

Project có thể nộp dưới dạng GitHub repository hoặc file zip hoàn chỉnh.