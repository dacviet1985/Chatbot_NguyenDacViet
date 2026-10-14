from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import setup_logging

setup_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(router)
