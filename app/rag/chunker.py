from __future__ import annotations

import uuid

from app.rag.types import RAGDocument


class TextChunker:
    """Character-based chunker with overlap and metadata preservation."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: list[RAGDocument]) -> list[RAGDocument]:
        chunks: list[RAGDocument] = []
        for document in documents:
            text = document.page_content.strip()
            if not text:
                continue
            start = 0
            chunk_index = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunk_text = text[start:end].strip()
                if chunk_text:
                    metadata = dict(document.metadata)
                    metadata["chunk_id"] = self._build_chunk_id(metadata, chunk_index)
                    metadata["chunk_index"] = chunk_index
                    chunks.append(RAGDocument(page_content=chunk_text, metadata=metadata))
                    chunk_index += 1
                if end >= len(text):
                    break
                start = max(0, end - self.chunk_overlap)
        return chunks

    def _build_chunk_id(self, metadata: dict[str, object], chunk_index: int) -> str:
        source = metadata.get("source", "unknown")
        page = metadata.get("page", "na")
        document_id = metadata.get("document_id", "unknown")
        seed = f"{document_id}:{source}:{page}:{chunk_index}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))
