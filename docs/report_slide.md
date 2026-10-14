# Slide: Báo cáo project (3–5 trang)

## END-TO-END RAG CHATBOT
### Trợ lý hỏi – đáp trên dữ liệu PDF/TXT

**Nội dung báo cáo chính**
- **Kiến trúc hệ thống**: Ingestion → Chunking → Embedding → Vector Store → Retrieval → LLM → Answer
- **Prompt template**: grounding, chống hallucination, chỉ trả lời theo context
- **Evaluation sheet**: 12 câu hỏi, Faithfulness = 1.0, Average Relevance = 1.917
- **Failure cases**: câu hỏi ngoài tài liệu, câu hỏi gần nghĩa nhưng thiếu context
- **Hướng dẫn chạy**: ingest, FastAPI, Streamlit, evaluation, test

**Điểm nổi bật**
- Hỗ trợ **citation/source**, **conversation memory**, **cache HIT/MISS**
- Có **tool calling**: calculator + weather
- Chạy được với **OpenAI thật** hoặc local fallback để test/demo

**File tham chiếu**
- `docs/report.md`
- `docs/architecture.md`
- `evaluation/evaluation_results.csv`
- `evaluation/failure_cases.md`
- `README.md`

---
**Gợi ý thuyết trình 20–30 giây**
> Báo cáo tập trung vào 5 phần chính: kiến trúc RAG end-to-end, prompt template chống hallucination, evaluation sheet với các chỉ số faithfulness và relevance, phân tích failure cases, và hướng dẫn chạy/demo hệ thống.
