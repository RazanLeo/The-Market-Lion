"""Structured logging via structlog (JSON in prod, pretty in dev)."""
from __future__ import annotations

import logging
import sys
import structlog
from .config import settings


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
    ]
    if settings.APP_ENV == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()
    structlog.configure(
        processors=shared + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
