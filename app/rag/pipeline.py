from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.cache import TTLCache
from app.core.config import Settings, get_settings
from app.rag.chunker import TextChunker
from app.rag.embeddings import BaseEmbedder, EmbeddingFactory
from app.rag.loader import DocumentLoader
from app.rag.memory import ConversationMemory
from app.rag.prompt import NO_ANSWER_TEXT, build_context, build_system_prompt, build_user_prompt
from app.rag.retriever import Retriever
from app.rag.types import IngestionStats, RAGDocument, RetrievedDocument
from app.tools.weather import WeatherTool
from app.rag.vector_store import FaissVectorStore, build_manifest, manifest_matches
from app.tools.calculator import CalculatorTool, ToolResult
from app.utils.text import deduplicate_sources, keyword_overlap_score, normalize_text, tokenize

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Coordinates ingestion, retrieval, generation, tool use, cache, and memory."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.loader = DocumentLoader(self.settings.knowledge_dir)
        self.chunker = TextChunker(self.settings.chunk_size, self.settings.chunk_overlap)
        self.embedder: BaseEmbedder = EmbeddingFactory.create(self.settings)
        self.vector_store = FaissVectorStore(
            store_path=self.settings.store_payload_path,
            index_path=self.settings.index_path,
            manifest_path=self.settings.manifest_path,
        )
        self.retriever = Retriever(self.vector_store, self.embedder, self.settings)
        self.memory = ConversationMemory(self.settings.memory_window)
        self.cache: TTLCache[dict[str, Any]] = TTLCache(self.settings.cache_ttl)
        self.calculator = CalculatorTool()
        self.weather = WeatherTool(timeout_seconds=self.settings.request_timeout)
        self._ensure_store_loaded()

    def ingest(self, force: bool = False) -> IngestionStats:
        start = time.perf_counter()
        files = self.loader.list_supported_files()
        if not files:
            raise RuntimeError("Knowledge folder đang rỗng. Hãy thêm file PDF/TXT trước khi ingest.")

        file_signatures = [self._file_signature(path) for path in files]
        manifest = build_manifest(
            file_signatures=file_signatures,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            model_name=self.embedder.model_name,
        )
        existing = self.vector_store.load_manifest()
        if not force and self.vector_store.exists() and manifest_matches(manifest, existing):
            self.vector_store.load()
            elapsed = time.perf_counter() - start
            chunk_count = len(self.vector_store.texts)
            stats = IngestionStats(
                files=len(files),
                documents=chunk_count,
                chunks=chunk_count,
                embedding_model=self.embedder.model_name,
                vector_store_location=str(self.settings.vector_store_dir),
                elapsed_seconds=round(elapsed, 3),
                reused_index=True,
            )
            logger.info("Ingestion reused existing vector store.")
            return stats

        documents = self.loader.load()
        if not documents:
            raise RuntimeError("Không tìm thấy nội dung hợp lệ trong Knowledge folder.")
        chunks = self.chunker.split_documents(documents)
        if not chunks:
            raise RuntimeError("Chunking không tạo ra dữ liệu. Hãy kiểm tra input documents.")

        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        vectors = self.embedder.embed_texts(texts)
        self.vector_store.save(texts, metadatas, vectors, manifest)
        elapsed = time.perf_counter() - start
        stats = IngestionStats(
            files=len(files),
            documents=len(documents),
            chunks=len(chunks),
            embedding_model=self.embedder.model_name,
            vector_store_location=str(self.settings.vector_store_dir),
            elapsed_seconds=round(elapsed, 3),
            reused_index=False,
        )
        logger.info("Ingestion completed: %s", stats)
        return stats

    def chat(self, session_id: str, message: str) -> dict[str, Any]:
        if not message.strip():
            raise ValueError("Empty query is not allowed.")

        start = time.perf_counter()
        history = self.memory.get_history(session_id)
        cached_payload = self._cache_lookup(message, history)
        if cached_payload is not None:
            logger.info("[CACHE] HIT | session=%s | query=%s", session_id, message)
            response = dict(cached_payload)
            response["cached"] = True
            response["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
            self._update_memory(session_id, message, response["answer"])
            return response
        logger.info("[CACHE] MISS | session=%s | query=%s", session_id, message)

        tool_result = self._maybe_run_tool(message)
        if tool_result is not None:
            answer = f"Kết quả từ calculator: {tool_result.output_text}"
            sources = tool_result.sources or []
            if tool_result.name == "weather":
                answer = tool_result.output_text
            response = {
                "answer": answer,
                "sources": sources,
                "cached": False,
                "tool_used": True,
                "tool_name": tool_result.name,
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
            self._cache_store(message, history, response)
            self._update_memory(session_id, message, answer)
            logger.info(
                "session=%s | query=%s | cache=MISS | retrieval=0 | tool=%s | latency=%.2fms | answer_status=tool",
                session_id,
                message,
                tool_result.name,
                response["latency_ms"],
            )
            logger.info("final_answer=%s", answer)
            return response

        self._ensure_store_loaded(auto_ingest=True)
        history = self.memory.get_history(session_id)
        transformed_query, documents = self.retriever.retrieve(message, history)
        sources = self._build_sources(documents)
        answer = self._generate_answer(message, session_id, transformed_query, documents)
        if answer == NO_ANSWER_TEXT and documents:
            answer = self._build_partial_match_explanation(message, documents)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        response = {
            "answer": answer,
            "sources": sources,
            "cached": False,
            "tool_used": False,
            "tool_name": None,
            "latency_ms": latency_ms,
        }
        self._cache_store(message, history, response)
        self._update_memory(session_id, message, answer)
        logger.info(
            "session=%s | query=%s | cache=MISS | retrieval=%s | tool=%s | latency=%.2fms | answer_status=%s",
            session_id,
            message,
            len(documents),
            "none",
            latency_ms,
            "grounded" if answer != NO_ANSWER_TEXT else "not_found",
        )
        logger.info("retrieved_documents=%s", json.dumps(sources, ensure_ascii=False))
        logger.info("final_answer=%s", answer)
        return response

    def clear_memory(self, session_id: str) -> None:
        self.memory.clear(session_id)

    def get_runtime_config(self) -> dict[str, Any]:
        return {
            "app_name": self.settings.app_name,
            "llm_provider": self.settings.llm_provider,
            "llm_model": self.settings.openai_model,
            "llm_mode": self.settings.llm_mode,
            "embedding_provider": self.settings.embedding_provider,
            "embedding_model": self.embedder.model_name,
            "embedding_mode": self.settings.embedding_mode,
            "real_ai_ready": self.settings.real_ai_ready,
            "has_openai_key": self.settings.has_openai_key,
            "top_k": self.settings.top_k,
            "temperature": self.settings.temperature,
            "chunk_size": self.settings.chunk_size,
            "chunk_overlap": self.settings.chunk_overlap,
            "cache_ttl": self.settings.cache_ttl,
        }

    def _cache_lookup(self, message: str, history: list[dict[str, str]]) -> dict[str, Any] | None:
        key = self._cache_key(message, history)
        return self.cache.get(key)

    def _cache_store(self, message: str, history: list[dict[str, str]], response: dict[str, Any]) -> None:
        key = self._cache_key(message, history)
        payload = {
            "answer": response["answer"],
            "sources": response["sources"],
            "cached": False,
            "tool_used": response["tool_used"],
            "tool_name": response.get("tool_name"),
        }
        self.cache.set(key, payload)

    def _cache_key(self, message: str, history: list[dict[str, str]]) -> str:
        transformed = self.retriever.transform_query(message, history)
        return normalize_text(transformed)

    def _maybe_run_tool(self, message: str):
        tools = [self.calculator, self.weather]
        for tool in tools:
            if not tool.can_handle(message):
                continue
            try:
                return tool.run(message)
            except ValueError as exc:
                logger.info("[TOOL] %s skipped | query=%s | reason=%s", tool.name, message, exc)
                if tool.name == "weather":
                    return ToolResult(
                        name=tool.name,
                        input_text=message,
                        output_text=str(exc),
                        sources=[],
                    )
                continue
        return None

    def _generate_answer(
        self,
        question: str,
        session_id: str,
        transformed_query: str,
        documents: list[RetrievedDocument],
    ) -> str:
        if not documents:
            return NO_ANSWER_TEXT
        if self.settings.llm_provider.lower() == "openai" and self.settings.openai_api_key:
            try:
                return self._generate_with_openai(question, session_id, transformed_query, documents)
            except Exception as exc:
                logger.exception("OpenAI LLM error, fallback to local answerer: %s", exc)
        return self._generate_with_local_grounding(transformed_query, documents)

    def _generate_with_openai(
        self,
        question: str,
        session_id: str,
        transformed_query: str,
        documents: list[RetrievedDocument],
    ) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key, timeout=self.settings.request_timeout)
        context = build_context(documents)
        prompt = build_user_prompt(question, self.memory.render_for_prompt(session_id), context)
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=self.settings.temperature,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
        )
        answer = response.choices[0].message.content or NO_ANSWER_TEXT
        if normalize_text(answer) == normalize_text(""):
            return NO_ANSWER_TEXT
        if answer.strip().lower().startswith("sources:"):
            return NO_ANSWER_TEXT
        if question and keyword_overlap_score(transformed_query, context) < self.settings.score_threshold:
            return NO_ANSWER_TEXT
        return answer.strip()

    def _generate_with_local_grounding(self, query: str, documents: list[RetrievedDocument]) -> str:
        sentences: list[tuple[float, str]] = []
        for document in documents:
            for sentence in self._split_sentences(document.page_content):
                lexical_score = keyword_overlap_score(query, sentence)
                if lexical_score >= 0.2:
                    sentences.append((lexical_score + document.score, sentence.strip()))
        if not sentences:
            return NO_ANSWER_TEXT
        ranked = sorted(sentences, key=lambda item: item[0], reverse=True)
        best_sentences: list[str] = []
        for _, sentence in ranked:
            if sentence not in best_sentences:
                best_sentences.append(sentence)
            if len(best_sentences) == 2:
                break
        if not best_sentences or ranked[0][0] < 0.35:
            return NO_ANSWER_TEXT
        return " ".join(best_sentences)

    def _build_sources(self, documents: list[RetrievedDocument]) -> list[dict[str, Any]]:
        items = [
            {
                "source": str(item.metadata.get("source", "unknown")),
                "page": item.metadata.get("page"),
                "score": item.score,
            }
            for item in documents
        ]
        return deduplicate_sources(items)

    def _build_partial_match_explanation(self, question: str, documents: list[RetrievedDocument]) -> str:
        sources = self._build_sources(documents)
        source_labels: list[str] = []
        for item in sources[:3]:
            label = str(item.get("source", "unknown"))
            page = item.get("page")
            if page:
                label = f"{label} trang {page}"
            source_labels.append(label)

        context_tokens = set(tokenize(build_context(documents)))
        missing_keywords: list[str] = []
        for token in tokenize(question):
            if token not in context_tokens and token not in missing_keywords:
                missing_keywords.append(token)

        source_text = ", ".join(source_labels) if source_labels else "các tài liệu đã tải"
        if missing_keywords:
            return (
                f"Tôi đã tìm thấy một số đoạn liên quan trong {source_text}, nhưng chưa có đủ thông tin trực tiếp để trả lời chính xác câu hỏi này. "
                f"Các từ khóa còn thiếu trong các đoạn tìm được: {', '.join(missing_keywords[:4])}. "
                "Bạn hãy hỏi cụ thể theo đúng tên văn bản/điều khoản đang có, hoặc tải thêm tài liệu phù hợp hơn."
            )

        return (
            f"Tôi đã tìm thấy một số đoạn liên quan trong {source_text}, nhưng nội dung hiện có vẫn chưa đủ để trả lời chắc chắn câu hỏi này. "
            "Bạn hãy hỏi hẹp hơn theo điều, khoản, loại thuế hoặc tên văn bản cụ thể."
        )

    def _ensure_store_loaded(self, auto_ingest: bool = False) -> None:
        if self.vector_store.exists():
            self.vector_store.load()
            return
        if auto_ingest:
            self.ingest(force=False)

    def _update_memory(self, session_id: str, question: str, answer: str) -> None:
        self.memory.add_message(session_id, "user", question)
        self.memory.add_message(session_id, "assistant", answer)

    def _split_sentences(self, text: str) -> list[str]:
        normalized = text.replace("\n", " ")
        pieces = [piece.strip() for piece in normalized.replace("?", ".").replace("!", ".").split(".")]
        return [piece for piece in pieces if piece]

    def _file_signature(self, path: Path) -> dict[str, Any]:
        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        }


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline(get_settings())
