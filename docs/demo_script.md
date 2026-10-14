# Demo script 3-5 phút

## Bước 1 - Giới thiệu Knowledge Base
- Thao tác: mở thư mục `Knowledge/`.
- Giải thích: có 2 file PDF và 1 file TXT.
- Điểm cần nói: hệ thống hỗ trợ ingest dữ liệu tùy chọn dạng PDF/TXT.

## Bước 2 - Chạy ingest
- Thao tác: chạy `python scripts/ingest.py`.
- Expected result: in ra số file, số documents, số chunks, embedding model, vector store location, thời gian ingest.
- Điểm cần nói: có manifest để tránh embed lại nếu dữ liệu không đổi.

## Bước 3 - Hỏi câu có trong tài liệu
- Câu hỏi: `Chính sách nghỉ phép năm là gì?`
- Expected result: trả lời đúng nội dung, có citation `sample_01.pdf`.
- Điểm cần nói: RAG trả lời grounded theo context.

## Bước 4 - Chứng minh citation
- Thao tác: chỉ vào phần Sources trên UI hoặc response API.
- Expected result: hiện `sample_01.pdf` và số trang.
- Điểm cần nói: không sinh citation giả.

## Bước 5 - Chứng minh memory
- Câu hỏi 1: `Chính sách nghỉ phép năm là gì?`
- Câu hỏi 2: `Còn nhân viên thử việc thì sao?`
- Expected result: bot hiểu follow-up và trả lời đúng về thử việc.
- Điểm cần nói: query transformation dùng lịch sử hội thoại để xử lý follow-up.

## Bước 6 - Chứng minh tool
- Câu hỏi: `184 * 12 * 5`
- Expected result: trả về `11040`, không cần retrieval.
- Điểm cần nói: calculator tool chạy trước RAG và có log riêng.

## Bước 6b - Chứng minh weather tool
- Câu hỏi: `thời tiết Hà Nội hôm nay`
- Expected result: trả về nhiệt độ, độ ẩm, gió, xác suất mưa; `tool=weather`.
- Điểm cần nói: weather tool lấy dữ liệu realtime từ API thời tiết, không phụ thuộc Knowledge Base.

## Bước 7 - Chứng minh chống hallucination
- Câu hỏi: `Công ty có hỗ trợ bảo hiểm cho thú cưng không?`
- Expected result: từ chối vì không có thông tin trong tài liệu.
- Điểm cần nói: prompt và local grounded answerer đều chặn bịa thông tin.

## Bước 8 - Chứng minh cache
- Thao tác: hỏi lại cùng một câu hỏi lần thứ hai.
- Expected result: response có `cached=true`, log hiện `[CACHE] HIT`.
- Điểm cần nói: cache TTL cấu hình qua `.env`.

## Bước 9 - Hiển thị log
- Thao tác: mở `logs/app.log`.
- Expected result: có query, retriever, cache, tool, latency, final answer.
- Điểm cần nói: phục vụ monitoring và debug.

## Bước 10 - Demo API
- Thao tác: gọi `GET /health` và `POST /chat`.
- Expected result: `/health` trả `{"status":"ok"}`; `/chat` trả answer, sources, cached, tool_used, latency.
- Điểm cần nói: backend FastAPI sẵn sàng để tích hợp frontend khác.

## Bước 11 - Kiểm tra sản phẩm nộp bài
- Thao tác: mở các thư mục `Knowledge/`, `evaluation/`, `docs/` và file `requirements.txt`.
- Expected result: có đủ mã nguồn, dữ liệu mẫu, báo cáo, evaluation sheet và kịch bản demo.
- Điểm cần nói: project đáp ứng đúng 4 hạng mục nộp bài trong slide yêu cầu.
