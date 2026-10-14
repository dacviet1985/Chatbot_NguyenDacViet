from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


def setup_logging() -> None:
    """Configure console and file logging once for the application."""

    settings = get_settings()
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
