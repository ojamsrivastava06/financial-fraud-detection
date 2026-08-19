"""
Transactions REST route endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.repository import TransactionRepository
from src.database.schemas import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionResponse], summary="List Transactions")
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Search by transaction ID, customer ID, or location"),
    fraud_only: Optional[bool] = Query(None, description="Filter for predicted fraud transactions only"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier: LOW, MEDIUM, HIGH"),
    merchant_category: Optional[str] = Query(None, description="Filter by merchant category"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    db: Session = Depends(get_db)
):
    """
    Fetch paginated transactions from database with filtering options.
    """
    repo = TransactionRepository(db)
    return repo.get_all(
        skip=skip,
        limit=limit,
        search=search,
        fraud_only=fraud_only,
        risk_level=risk_level,
        merchant_category=merchant_category,
        payment_method=payment_method
    )


@router.get("/{transaction_id}", response_model=TransactionResponse, summary="Get Transaction Details")
def get_transaction_by_id(transaction_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single transaction record by unique Transaction ID.
    """
    repo = TransactionRepository(db)
    tx = repo.get_by_transaction_id(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    return tx
