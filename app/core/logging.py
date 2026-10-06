"""Application logging configuration with a small, safe default format."""

import logging

from app.core.config import settings


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), None)
    if not isinstance(level, int):
        raise ValueError("LOG_LEVEL must be a valid Python logging level")
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
