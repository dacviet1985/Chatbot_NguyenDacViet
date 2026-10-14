from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils.pdf_generator import write_simple_pdf


KNOWLEDGE_DIR = ROOT / "Knowledge"


if __name__ == "__main__":
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    write_simple_pdf(
        KNOWLEDGE_DIR / "sample_01.pdf",
        [
            "Chính sách nghỉ phép năm.\nNhân viên chính thức có 12 ngày nghỉ phép năm hưởng lương.\nNhân viên thử việc chưa có ngày nghỉ phép năm nhưng có thể xin nghỉ không lương khi được quản lý phê duyệt.",
            "Quy trình nghỉ phép.\nNhân viên cần gửi đơn nghỉ phép trên hệ thống HR trước ít nhất 3 ngày làm việc.\nQuản lý trực tiếp phải phản hồi trong vòng 1 ngày làm việc.",
        ],
    )
    write_simple_pdf(
        KNOWLEDGE_DIR / "sample_02.pdf",
        [
            "Quy định thiết bị văn phòng.\nNhân viên phải tắt máy tính xách tay và khóa ngăn kéo trước khi rời văn phòng.\nSự cố thiết bị phải được báo cho bộ phận IT trong vòng 30 phút kể từ khi phát hiện.",
            "Xử lý sự cố sau giờ làm việc.\nNếu quên tắt máy tính, nhân viên phải báo cho IT hoặc bảo vệ trực ca để hỗ trợ xử lý thiết bị sau giờ làm việc.",
        ],
    )
    print("Sample PDFs generated in Knowledge/")
