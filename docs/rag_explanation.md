# Giải thích lựa chọn RAG

## 1. Chunk size = 800

Lý do:
- Đủ lớn để giữ trọn ý nghĩa của policy, guideline, quy trình ngắn.
- Không quá lớn để làm retrieval bị nhiễu.
- Phù hợp tài liệu nội bộ dạng handbook hoặc SOP.

Nếu chunk quá nhỏ:
- Mất context.
- Câu trả lời dễ thiếu thông tin hoặc thiếu citation đúng.

Nếu chunk quá lớn:
- Similarity search kém chính xác hơn.
- Prompt dài, tốn token, tăng độ nhiễu.

## 2. Chunk overlap = 120

Lý do:
- Giảm mất mát thông tin ở ranh giới chunk.
- Hữu ích với các câu quy định kéo dài qua nhiều dòng hoặc nhiều đoạn.

Nếu overlap quá thấp:
- Dễ mất ý giữa hai chunk.

Nếu overlap quá cao:
- Trùng lặp nhiều, tăng chi phí embedding và noise retrieval.

## 3. Embedding model

Mặc định:
- OpenAI `text-embedding-3-small`

Lý do:
- Ổn định, phổ biến, chất lượng tốt cho semantic search.
- Dễ cấu hình qua `.env`.

Tùy chọn local:
- HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- Local hash fallback cho môi trường test/offline.

## 4. Top-K = 5

Lý do:
- Đủ rộng để gom các chunk liên quan.
- Không quá cao để đưa quá nhiều noise vào prompt.

Nếu Top-K quá thấp:
- Thiếu context, đặc biệt với câu hỏi cần nhiều nguồn.

Nếu Top-K quá cao:
- Prompt dài hơn.
- Nhiều chunk không liên quan làm giảm chất lượng trả lời.

## 5. Query transformation

Project có bonus `USE_QUERY_TRANSFORMATION=true`.

Mục tiêu:
- Hỗ trợ follow-up question như `Còn nhân viên thử việc thì sao?`
- Tận dụng lịch sử hội thoại để mở rộng query trước khi retrieve.

Ưu điểm:
- Dễ triển khai.
- Nhẹ hơn reranker.
- Phù hợp demo module cuối kỳ.
