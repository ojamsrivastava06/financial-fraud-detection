"""
FastAPI dependency injection utilities.
"""

from src.database.connection import get_db

__all__ = ["get_db"]
