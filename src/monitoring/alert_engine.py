"""
Alert engine service for triggering security alerts on high/medium risk predictions.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.database.models import AlertModel
from src.database.repository import AlertRepository
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlertEngine:
    """Evaluates prediction probability and triggers alerts in database repository."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def evaluate_and_trigger_alert(
        self,
        transaction_id: str,
        risk_level: str,
        probability: float,
        risk_score: float,
        db: Optional[Session] = None
    ) -> Optional[AlertModel]:
        """
        Triggers security alert based on prediction risk score tier.

        HIGH risk (>= 0.65) -> CRITICAL / HIGH Alert
        MEDIUM risk (0.35 to 0.65) -> MEDIUM Alert
        LOW risk (< 0.35) -> No Alert
        """
        session = db or self.db
        if session is None:
            logger.warning(f"No database session provided for alert evaluation on transaction {transaction_id}")
            return None

        alert_repo = AlertRepository(session)

        if risk_level == "HIGH":
            severity = "CRITICAL" if probability >= 0.85 else "HIGH"
            msg = f"High-risk transaction detected: {probability * 100:.1f}% fraud probability."
            return alert_repo.create_alert(
                transaction_id=transaction_id,
                severity=severity,
                fraud_probability=probability,
                risk_score=risk_score,
                message=msg
            )
        elif risk_level == "MEDIUM":
            severity = "MEDIUM"
            msg = f"Elevated-risk transaction monitored: {probability * 100:.1f}% fraud probability."
            return alert_repo.create_alert(
                transaction_id=transaction_id,
                severity=severity,
                fraud_probability=probability,
                risk_score=risk_score,
                message=msg
            )
        else:
            # LOW risk -> No alert created
            return None
