"""
Logger retrieval utility.
"""

import logging
from src.config.logging_config import setup_logging


def get_logger(name: str = "fraud_detection") -> logging.Logger:
    """Retrieve a configured module logger."""
    return logging.getLogger(name)
