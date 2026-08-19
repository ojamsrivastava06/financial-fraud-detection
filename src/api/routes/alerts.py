"""
Security Alerts REST route endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.repository import AlertRepository
from src.database.schemas import AlertResponse, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertResponse], summary="List Security Alerts")
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by alert status: OPEN, INVESTIGATING, RESOLVED, DISMISSED"),
    severity: Optional[str] = Query(None, description="Filter by severity: MEDIUM, HIGH, CRITICAL"),
    db: Session = Depends(get_db)
):
    """
    Fetch paginated security alerts with filtering.
    """
    repo = AlertRepository(db)
    return repo.get_all_alerts(status=status, severity=severity, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=AlertResponse, summary="Get Alert Details")
def get_alert_by_id(alert_id: int, db: Session = Depends(get_db)):
    """
    Retrieve single alert details by primary ID.
    """
    repo = AlertRepository(db)
    alert = repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found.")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse, summary="Update Alert Status")
def update_alert_status(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)):
    """
    Update security alert status (OPEN -> INVESTIGATING -> RESOLVED / DISMISSED).
    """
    repo = AlertRepository(db)
    try:
        updated_alert = repo.update_status(alert_id, payload.status, payload.resolution_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not updated_alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert #{alert_id} not found.")
    return updated_alert
