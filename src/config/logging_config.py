"""
Structured logging configuration module.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configures structured application logging across modules."""
    log_level = level.upper() if level else "INFO"
    numeric_level = getattr(logging, log_level, logging.INFO)

    log_format = (
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logger = logging.getLogger("fraud_detection")
    logger.setLevel(numeric_level)
    return logger
