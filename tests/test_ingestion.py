from __future__ import annotations

from app.rag.chunker import TextChunker
from app.rag.loader import DocumentLoader
from app.utils.pdf_generator import write_simple_pdf


def test_document_loader_supports_pdf_and_txt(tmp_path):
    knowledge_dir = tmp_path / "Knowledge"
    knowledge_dir.mkdir()
    txt_file = knowledge_dir / "manual.txt"
    txt_file.write_text("Quy trình xin nghỉ phép trước 3 ngày làm việc.", encoding="utf-8")
    pdf_file = knowledge_dir / "policy.pdf"
    write_simple_pdf(pdf_file, ["Nhân viên chính thức có 12 ngày nghỉ phép năm."])

    loader = DocumentLoader(knowledge_dir)
    documents = loader.load()

    assert len(documents) == 2
    assert {doc.metadata["source"] for doc in documents} == {"manual.txt", "policy.pdf"}
    assert any(doc.metadata["page"] == 1 for doc in documents if doc.metadata["source"] == "policy.pdf")


def test_chunker_preserves_metadata_and_adds_chunk_id():
    documents = [
        loader_doc("A" * 1200, {"source": "manual.txt", "page": None, "document_id": "doc-1"})
    ]
    chunker = TextChunker(chunk_size=300, chunk_overlap=50)

    chunks = chunker.split_documents(documents)

    assert len(chunks) >= 4
    assert all(chunk.metadata["source"] == "manual.txt" for chunk in chunks)
    assert all("chunk_id" in chunk.metadata for chunk in chunks)


def loader_doc(text, metadata):
    from app.rag.types import RAGDocument

    return RAGDocument(page_content=text, metadata=metadata)
