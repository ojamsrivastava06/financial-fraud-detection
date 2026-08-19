"""
Risk scoring and probability categorization module.
Maps model probability predictions into risk scores and risk level tiers.
"""

from typing import Dict, Any, Optional
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_risk_score(
    probability: float,
    high_risk_threshold: Optional[float] = None,
    medium_risk_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes risk score and risk level for a transaction probability prediction.

    Args:
        probability: Fraud probability between 0.0 and 1.0.
        high_risk_threshold: Threshold above which transaction is flagged HIGH risk.
        medium_risk_threshold: Threshold above which transaction is flagged MEDIUM risk.

    Returns:
        Dict containing probability, percentage, score, risk_level, and recommended action.
    """
    if probability is None or not (0.0 <= probability <= 1.0):
        return {
            "fraud_probability": 0.0,
            "fraud_percentage": 0.0,
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "fraud_prediction": 0,
            "action": "AWAIT_INFERENCE"
        }

    high_th = high_risk_threshold if high_risk_threshold is not None else settings.HIGH_RISK_THRESHOLD
    med_th = medium_risk_threshold if medium_risk_threshold is not None else settings.MEDIUM_RISK_THRESHOLD

    fraud_pct = round(probability * 100.0, 2)
    risk_score = round(probability * 100.0, 1)

    if probability >= high_th:
        risk_level = "HIGH"
        fraud_prediction = 1
        action = "FLAG_FOR_REVIEW"
    elif probability >= med_th:
        risk_level = "MEDIUM"
        fraud_prediction = 1 if probability >= 0.50 else 0
        action = "MONITOR"
    else:
        risk_level = "LOW"
        fraud_prediction = 0
        action = "APPROVE"

    return {
        "fraud_probability": round(float(probability), 4),
        "fraud_percentage": fraud_pct,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "fraud_prediction": fraud_prediction,
        "action": action
    }
