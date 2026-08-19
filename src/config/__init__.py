"""
Configuration management package for Financial Fraud Detection Platform.
"""

from src.config.settings import settings
from src.config.logging_config import setup_logging

__all__ = ["settings", "setup_logging"]
