"""
API router endpoints package.
"""

from src.api.routes.health import router as health_router
from src.api.routes.transactions import router as transactions_router
from src.api.routes.predictions import router as predictions_router
from src.api.routes.analytics import router as analytics_router
from src.api.routes.alerts import router as alerts_router

__all__ = [
    "health_router",
    "transactions_router",
    "predictions_router",
    "analytics_router",
    "alerts_router",
]
