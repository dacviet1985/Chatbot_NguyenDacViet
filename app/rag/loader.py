from __future__ import annotations

import logging
import uuid
from pathlib import Path

from pypdf import PdfReader

from app.rag.types import RAGDocument

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


class DocumentLoader:
    """Loads supported documents from the knowledge directory."""

    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir

    def list_supported_files(self) -> list[Path]:
        files = [
            path
            for path in sorted(self.knowledge_dir.iterdir())
            if path.is_file() and path.suffix.lower() in _SUPPORTED_EXTENSIONS
        ]
        return files

    def load(self) -> list[RAGDocument]:
        documents: list[RAGDocument] = []
        for file_path in self.list_supported_files():
            try:
                if file_path.suffix.lower() == ".pdf":
                    documents.extend(self._load_pdf(file_path))
                elif file_path.suffix.lower() == ".txt":
                    documents.extend(self._load_txt(file_path))
            except Exception as exc:
                logger.exception("Không thể đọc file %s: %s", file_path.name, exc)
        return documents

    def _load_pdf(self, file_path: Path) -> list[RAGDocument]:
        reader = PdfReader(str(file_path))
        document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(file_path.resolve())))
        documents: list[RAGDocument] = []
        for index, page in enumerate(reader.pages, start=1):
            text = self._repair_text((page.extract_text() or "").strip())
            if not text:
                continue
            documents.append(
                RAGDocument(
                    page_content=text,
                    metadata={
                        "source": file_path.name,
                        "page": index,
                        "document_id": document_id,
                    },
                )
            )
        return documents

    def _load_txt(self, file_path: Path) -> list[RAGDocument]:
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(file_path.resolve())))
        return [
            RAGDocument(
                page_content=text,
                metadata={
                    "source": file_path.name,
                    "page": None,
                    "document_id": document_id,
                },
            )
        ]

    def _repair_text(self, text: str) -> str:
        if "Ã" not in text and "á»" not in text:
            return text
        try:
            repaired = text.encode("latin1").decode("utf-8")
            return repaired
        except UnicodeError:
            return text
