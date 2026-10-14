from __future__ import annotations

from app.rag.types import RetrievedDocument


NO_ANSWER_TEXT = "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong tài liệu được cung cấp."


def build_context(documents: list[RetrievedDocument]) -> str:
    parts: list[str] = []
    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")
        page = document.metadata.get("page")
        page_text = f", page {page}" if page else ""
        parts.append(f"[{index}] {source}{page_text}\n{document.page_content}")
    return "\n\n".join(parts)


def build_system_prompt() -> str:
    return (
        "Bạn là trợ lý RAG chỉ được phép trả lời bằng thông tin trong CONTEXT. "
        "Nếu CONTEXT không đủ, hãy trả lời đúng một câu: "
        f"'{NO_ANSWER_TEXT}'. "
        "Không được suy diễn, không được tạo citation giả, không sử dụng kiến thức ngoài."
    )


def build_user_prompt(question: str, memory_snippet: str, context: str) -> str:
    return (
        "Hãy trả lời trực tiếp bằng tiếng Việt.\n"
        "Chỉ dùng thông tin trong CONTEXT.\n"
        "Nếu không có thông tin thì trả lời đúng câu từ chối được chỉ định.\n"
        "Không tạo nguồn giả.\n\n"
        f"MEMORY:\n{memory_snippet or 'Không có'}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context or 'Không có'}"
    )
