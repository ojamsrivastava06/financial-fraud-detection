"""
Helper functions for formatting, directory verification, and file operations.
"""

from pathlib import Path
from typing import Union
from src.utils.logger import get_logger

logger = get_logger(__name__)


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """Ensure directory exists on disk."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def format_currency(amount: float) -> str:
    """Format floating point amount to standard currency string."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format decimal value to percentage string."""
    return f"{value * 100:.2f}%"
