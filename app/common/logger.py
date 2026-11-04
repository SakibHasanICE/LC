"""
Centralized logger setup for the app.

Usage:
    from app.common.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys
from pathlib import Path

from app.config.settings import settings

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured — avoid duplicate handlers on repeated imports
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_DIR / "app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger