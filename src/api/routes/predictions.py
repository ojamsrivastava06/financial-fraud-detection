"""
Predictions REST route endpoints for single and batch model inference.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.connection import get_db
from src.database.schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
)
from src.config.settings import settings
from src.monitoring.fraud_monitor import FraudMonitor

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/predict", response_model=PredictionResponse, summary="Predict Fraud for Transaction")
def predict_transaction(payload: PredictionRequest, db: Session = Depends(get_db)):
    """
    Evaluates fraud risk probability for a single transaction payload.
    Executes feature engineering, preprocessor transformation, ML model inference,
    risk scoring, database persistence, and security alert generation.
    """
    tx_dict = payload.transaction.model_dump()
    monitor = FraudMonitor(db)
    result = monitor.process_transaction(tx_dict, db=db)

    if result.get("status") == "model_not_loaded":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Model not available. Run training pipeline first."
        )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Prediction error.")
        )

    return PredictionResponse(
        transaction_id=result["transaction_id"],
        fraud_probability=result["fraud_probability"],
        fraud_percentage=result["fraud_percentage"],
        fraud_prediction=result["fraud_prediction"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        action=result["action"],
        threshold_used=result.get("operating_threshold", 0.65),
        model_name=result.get("model_name", "LogisticRegression")
    )


@router.post("/batch", response_model=BatchPredictionResponse, summary="Batch Fraud Prediction")
def predict_batch_transactions(payload: BatchPredictionRequest, db: Session = Depends(get_db)):
    """
    Batch transaction prediction endpoint.
    Processes list of transactions, returning predictions for valid items
    and detailed error messages for invalid ones without crashing the batch.
    """
    if len(payload.transactions) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch transactions list cannot be empty."
        )

    if len(payload.transactions) > settings.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Batch size of {len(payload.transactions)} exceeds maximum allowed limit of {settings.MAX_BATCH_SIZE} transactions."
        )
    monitor = FraudMonitor(db)
    successful = []
    errors = []

    for idx, tx_item in enumerate(payload.transactions):
        try:
            tx_dict = tx_item.model_dump()
            res = monitor.process_transaction(tx_dict, db=db)
            if res.get("status") == "error":
                errors.append({"index": idx, "transaction_id": tx_dict.get("transaction_id"), "error": res.get("message", "Prediction error.")})
            elif res.get("status") == "model_not_loaded":
                errors.append({"index": idx, "transaction_id": tx_dict.get("transaction_id"), "error": "ML model not loaded."})
            else:
                successful.append(PredictionResponse(
                    transaction_id=res["transaction_id"],
                    fraud_probability=res["fraud_probability"],
                    fraud_percentage=res["fraud_percentage"],
                    fraud_prediction=res["fraud_prediction"],
                    risk_score=res["risk_score"],
                    risk_level=res["risk_level"],
                    action=res["action"],
                    threshold_used=res.get("operating_threshold", 0.65),
                    model_name=res.get("model_name", "LogisticRegression")
                ))
        except Exception as e:
            errors.append({"index": idx, "transaction_id": tx_item.transaction_id if hasattr(tx_item, 'transaction_id') else None, "error": str(e)})

    return BatchPredictionResponse(
        total_submitted=len(payload.transactions),
        successful_predictions=len(successful),
        failed_predictions=len(errors),
        predictions=successful,
        errors=errors
    )
