"""
Logging configuration for face detection pipeline.

Uses structlog for structured, JSON-formatted logging with context binding.
"""

import structlog
import logging
import sys


def setup_logging():
    """Initialize structlog configuration."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure Python's standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger bound to a specific module."""
    return structlog.get_logger(name)


def bind_context(**kwargs) -> structlog.BoundLogger:
    """Create a logger bound to context variables (session_id, frame_id, etc.)."""
    logger = structlog.get_logger()
    return logger.bind(**kwargs)
