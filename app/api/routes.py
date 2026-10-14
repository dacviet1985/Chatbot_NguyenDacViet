from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from app.rag.pipeline import get_rag_pipeline
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ClearMemoryResponse,
    ConfigResponse,
    HealthResponse,
    IngestResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    pipeline = get_rag_pipeline()
    return ConfigResponse(**pipeline.get_runtime_config())


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.chat(session_id=request.session_id, message=request.message)
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("Unhandled /chat error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/admin/rebuild", response_model=IngestResponse)
def rebuild_index(force: bool = Query(default=True)) -> IngestResponse:
    try:
        pipeline = get_rag_pipeline()
        stats = pipeline.ingest(force=force)
        return IngestResponse(**asdict(stats))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/memory/{session_id}/clear", response_model=ClearMemoryResponse)
def clear_memory(session_id: str) -> ClearMemoryResponse:
    pipeline = get_rag_pipeline()
    pipeline.clear_memory(session_id)
    return ClearMemoryResponse(status="cleared", session_id=session_id)
