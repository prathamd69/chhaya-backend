import logging
import os
import sys
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_FORMAT = "[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s"

# Handlers are created ONCE here and shared by every logger
_formatter = logging.Formatter(LOG_FORMAT)
_handlers = []

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_formatter)
_handlers.append(_stream_handler)

if settings.LOG_TO_FILE:
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    _file_handler = RotatingFileHandler(
        log_dir / "application.log", maxBytes=5_000_000, backupCount=3
    )
    _file_handler.setFormatter(_formatter)
    _handlers.append(_file_handler)


def configLogger(loggerName: str) -> Logger:
    """Always call as configLogger(__file__)."""
    try:
        name = os.path.relpath(loggerName, PROJECT_ROOT).replace(os.sep, ".").removesuffix(".py")
    except Exception:
        name = os.path.basename(loggerName).removesuffix(".py")

    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper())
    logger.propagate = False

    if not logger.handlers:
        for handler in _handlers:
            logger.addHandler(handler)

    return logger