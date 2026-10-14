# Failure Case 1

Question:
Công ty có hỗ trợ bảo hiểm cho thú cưng không?

Expected behavior:
Bot phải trả lời không tìm thấy thông tin phù hợp trong tài liệu được cung cấp.

Actual behavior:
Script evaluation cần xác nhận bot từ chối trả lời ngoài ngữ cảnh.

Root cause:
Knowledge Base không chứa chính sách bảo hiểm cho thú cưng.

Improvement:
Bổ sung tài liệu HR benefits nếu muốn hỗ trợ câu hỏi này.

# Failure Case 2

Question:
Laptop bị treo vào cuối ngày thì có được mang về nhà sửa không?

Expected behavior:
Bot không được tự suy diễn. Nếu context không đề cập việc mang laptop về nhà, bot phải từ chối hoặc chỉ trả lời phần được tài liệu hỗ trợ.

Actual behavior:
Hệ thống local fallback có thể chỉ trích dẫn quy định báo IT và tắt máy, không khẳng định hành động mang về nhà.

Root cause:
Từ khóa gần giống "laptop" và "sửa" có thể kéo về chunk liên quan thiết bị nhưng không đủ context chi tiết.

Improvement:
Thêm reranker hoặc query transformation nâng cao, đồng thời mở rộng tài liệu quy trình xử lý thiết bị.
