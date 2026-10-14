from __future__ import annotations

import os
from pathlib import Path

import requests
import streamlit as st

def resolve_api_base_url() -> str:
    try:
        return st.secrets.get("API_BASE_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    except Exception:
        return os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


API_BASE_URL = resolve_api_base_url()
KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "Knowledge"

st.set_page_config(page_title="RAG Knowledge Assistant", page_icon="🤖", layout="wide")


def fetch_config() -> dict:
    response = requests.get(f"{API_BASE_URL}/config", timeout=30)
    response.raise_for_status()
    return response.json()


def upload_files(uploaded_files: list) -> None:
    for uploaded in uploaded_files:
        target = KNOWLEDGE_DIR / uploaded.name
        target.write_bytes(uploaded.getbuffer())


def post_json(path: str, payload: dict | None = None) -> dict:
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


config = fetch_config()
st.sidebar.title("⚙️ Cấu hình")
st.sidebar.write(f"Ứng dụng: {config['app_name']}")
st.sidebar.write(f"LLM: {config['llm_model']} ({config['llm_provider']})")
st.sidebar.write(f"LLM mode: {config['llm_mode']}")
st.sidebar.write(f"Embedding: {config['embedding_model']} ({config['embedding_provider']})")
st.sidebar.write(f"Embedding mode: {config['embedding_mode']}")
if config["real_ai_ready"]:
    st.sidebar.success("Real AI: READY")
else:
    st.sidebar.warning("Real AI: chưa sẵn sàng - thêm OPENAI_API_KEY vào .env")
st.sidebar.write(f"Top K: {config['top_k']}")
st.sidebar.write(f"Temperature: {config['temperature']}")
st.sidebar.write(f"Chunk size: {config['chunk_size']}")
st.sidebar.write(f"Chunk overlap: {config['chunk_overlap']}")
st.sidebar.write(f"Cache TTL: {config['cache_ttl']} giây")

session_id = st.sidebar.text_input("Session ID", value="demo001")
uploaded_files = st.sidebar.file_uploader(
    "Upload PDF/TXT vào Knowledge/",
    type=["pdf", "txt"],
    accept_multiple_files=True,
)
if uploaded_files:
    upload_files(uploaded_files)
    st.sidebar.success("Đã lưu file vào Knowledge/.")

if st.sidebar.button("Rebuild index"):
    result = post_json("/admin/rebuild?force=true")
    st.sidebar.success(
        f"Rebuild xong: {result['files']} files, {result['chunks']} chunks, reused={result['reused_index']}"
    )

if st.sidebar.button("Clear Conversation"):
    post_json(f"/memory/{session_id}/clear")
    st.session_state["messages"] = []
    st.sidebar.success("Đã xóa conversation.")

st.title("🤖 RAG Knowledge Assistant")
st.caption("Trợ lý hỏi – đáp trên dữ liệu PDF/TXT với citation, memory, cache và calculator tool.")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.markdown("**Sources**")
            for source in message["sources"]:
                page = source.get("page")
                page_text = f" - Page {page}" if page else ""
                st.write(f"📄 {source['source']}{page_text}")
        if message.get("meta"):
            meta = message["meta"]
            st.caption(
                f"Latency: {meta['latency_ms']} ms | Cache: {'HIT' if meta['cached'] else 'MISS'} | Tool: {meta.get('tool_name') or 'none'}"
            )

prompt = st.chat_input("Nhập câu hỏi...")
if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            result = post_json("/chat", {"session_id": session_id, "message": prompt})
        st.markdown(result["answer"])
        if result["sources"]:
            st.markdown("**Sources**")
            for source in result["sources"]:
                page = source.get("page")
                page_text = f" - Page {page}" if page else ""
                st.write(f"📄 {source['source']}{page_text}")
        st.caption(
            f"Latency: {result['latency_ms']} ms | Cache: {'HIT' if result['cached'] else 'MISS'} | Tool: {result.get('tool_name') or 'none'}"
        )
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "meta": {
                "latency_ms": result["latency_ms"],
                "cached": result["cached"],
                "tool_used": result["tool_used"],
                "tool_name": result.get("tool_name"),
            },
        }
    )
