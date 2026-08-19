"""
Analytics & Time-Series metrics REST route endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.repository import TransactionRepository
from src.database.schemas import AnalyticsSummary, TimeSeriesAnalytics, TimeSeriesDataPoint

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary, summary="Fraud Analytics Summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Returns dynamically calculated fraud detection metrics from database.
    """
    repo = TransactionRepository(db)
    summary_data = repo.get_analytics_summary()
    return AnalyticsSummary(**summary_data)


@router.get("/time-series", response_model=TimeSeriesAnalytics, summary="Time-Series Trend Analytics")
def get_time_series_analytics(db: Session = Depends(get_db)):
    """
    Returns daily transaction volume, fraud count, and risk breakdown time-series.
    """
    repo = TransactionRepository(db)
    ts_data = repo.get_time_series_analytics()
    data_points = [TimeSeriesDataPoint(**item) for item in ts_data]
    return TimeSeriesAnalytics(period="daily", data_points=data_points)
