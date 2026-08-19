"""
Database Repository layer for Transactions, Predictions, Security Alerts, and Analytics queries.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from src.database.models import TransactionModel, PredictionModel, AlertModel
from src.database.schemas import TransactionCreate
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionRepository:
    """Repository encapsulating database query operations for transactions."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_transaction_id(self, transaction_id: str) -> Optional[TransactionModel]:
        """Fetch transaction by unique transaction ID."""
        return (
            self.db.query(TransactionModel)
            .filter(TransactionModel.transaction_id == transaction_id)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        fraud_only: Optional[bool] = None,
        risk_level: Optional[str] = None,
        merchant_category: Optional[str] = None,
        payment_method: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[TransactionModel]:
        """Fetch paginated transactions list with search and filters."""
        query = self.db.query(TransactionModel)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TransactionModel.transaction_id.ilike(search_pattern),
                    TransactionModel.customer_id.ilike(search_pattern),
                    TransactionModel.location.ilike(search_pattern)
                )
            )

        if fraud_only is True:
            query = query.filter(TransactionModel.fraud_prediction == 1)

        if risk_level:
            query = query.filter(TransactionModel.risk_level == risk_level.upper())

        if merchant_category:
            query = query.filter(TransactionModel.merchant_category == merchant_category)

        if payment_method:
            query = query.filter(TransactionModel.payment_method == payment_method)

        if date_from:
            query = query.filter(TransactionModel.transaction_date >= date_from)

        if date_to:
            query = query.filter(TransactionModel.transaction_date <= date_to)

        return query.order_by(desc(TransactionModel.id)).offset(skip).limit(limit).all()

    def count(
        self,
        search: Optional[str] = None,
        fraud_only: Optional[bool] = None,
        risk_level: Optional[str] = None,
        merchant_category: Optional[str] = None,
        payment_method: Optional[str] = None
    ) -> int:
        """Get count of matching transaction records."""
        query = self.db.query(func.count(TransactionModel.id))

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TransactionModel.transaction_id.ilike(search_pattern),
                    TransactionModel.customer_id.ilike(search_pattern)
                )
            )

        if fraud_only is True:
            query = query.filter(TransactionModel.fraud_prediction == 1)

        if risk_level:
            query = query.filter(TransactionModel.risk_level == risk_level.upper())

        if merchant_category:
            query = query.filter(TransactionModel.merchant_category == merchant_category)

        if payment_method:
            query = query.filter(TransactionModel.payment_method == payment_method)

        return query.scalar() or 0

    def create_or_update(
        self,
        transaction_data: Dict[str, Any],
        prediction_info: Optional[Dict[str, Any]] = None
    ) -> TransactionModel:
        """
        Idempotent insert or update for transaction record.
        """
        tx_id = transaction_data["transaction_id"]
        existing = self.get_by_transaction_id(tx_id)

        if existing:
            # Update fields
            for key, value in transaction_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            if prediction_info:
                existing.fraud_probability = prediction_info.get("fraud_probability")
                existing.fraud_prediction = prediction_info.get("fraud_prediction")
                existing.risk_score = prediction_info.get("risk_score")
                existing.risk_level = prediction_info.get("risk_level")
                existing.prediction_timestamp = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        db_obj = TransactionModel(**transaction_data)
        if prediction_info:
            db_obj.fraud_probability = prediction_info.get("fraud_probability")
            db_obj.fraud_prediction = prediction_info.get("fraud_prediction")
            db_obj.risk_score = prediction_info.get("risk_score")
            db_obj.risk_level = prediction_info.get("risk_level")
            db_obj.prediction_timestamp = datetime.now(timezone.utc)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Calculates dynamic aggregate metrics across stored transactions."""
        total_tx = self.db.query(func.count(TransactionModel.id)).scalar() or 0
        if total_tx == 0:
            return {
                "total_transactions": 0,
                "total_fraud_predictions": 0,
                "total_legitimate_predictions": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
                "fraud_rate_pct": 0.0,
                "total_transaction_value": 0.0,
                "high_risk_value": 0.0,
                "average_transaction_value": 0.0,
            }

        fraud_preds = self.db.query(func.count(TransactionModel.id)).filter(TransactionModel.fraud_prediction == 1).scalar() or 0
        legit_preds = total_tx - fraud_preds

        high_count = self.db.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "HIGH").scalar() or 0
        med_count = self.db.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "MEDIUM").scalar() or 0
        low_count = self.db.query(func.count(TransactionModel.id)).filter(TransactionModel.risk_level == "LOW").scalar() or 0

        total_val = self.db.query(func.sum(TransactionModel.transaction_amount)).scalar() or 0.0
        high_val = self.db.query(func.sum(TransactionModel.transaction_amount)).filter(TransactionModel.risk_level == "HIGH").scalar() or 0.0
        avg_val = total_val / total_tx if total_tx > 0 else 0.0
        fraud_rate = (fraud_preds / total_tx) * 100.0

        return {
            "total_transactions": total_tx,
            "total_fraud_predictions": fraud_preds,
            "total_legitimate_predictions": legit_preds,
            "high_risk_count": high_count,
            "medium_risk_count": med_count,
            "low_risk_count": low_count,
            "fraud_rate_pct": round(fraud_rate, 2),
            "total_transaction_value": round(float(total_val), 2),
            "high_risk_value": round(float(high_val), 2),
            "average_transaction_value": round(float(avg_val), 2),
        }

    def get_time_series_analytics(self) -> List[Dict[str, Any]]:
        """Computes daily aggregated transaction volume and risk distribution."""
        from sqlalchemy import case

        results = (
            self.db.query(
                TransactionModel.transaction_date,
                func.count(TransactionModel.id).label("total_count"),
                func.sum(case((TransactionModel.fraud_prediction == 1, 1), else_=0)).label("fraud_count"),
                func.sum(case((TransactionModel.risk_level == "HIGH", 1), else_=0)).label("high_risk_count"),
                func.sum(case((TransactionModel.risk_level == "MEDIUM", 1), else_=0)).label("medium_risk_count"),
                func.sum(case((TransactionModel.risk_level == "LOW", 1), else_=0)).label("low_risk_count"),
                func.sum(TransactionModel.transaction_amount).label("total_amount"),
                func.sum(case((TransactionModel.fraud_prediction == 1, TransactionModel.transaction_amount), else_=0.0)).label("fraud_amount")
            )
            .group_by(TransactionModel.transaction_date)
            .order_by(TransactionModel.transaction_date)
            .all()
        )

        output = []
        for r in results:
            output.append({
                "date": str(r.transaction_date),
                "total_count": int(r.total_count or 0),
                "fraud_count": int(r.fraud_count or 0),
                "high_risk_count": int(r.high_risk_count or 0),
                "medium_risk_count": int(r.medium_risk_count or 0),
                "low_risk_count": int(r.low_risk_count or 0),
                "total_amount": round(float(r.total_amount or 0.0), 2),
                "fraud_amount": round(float(r.fraud_amount or 0.0), 2)
            })
        return output


class PredictionRepository:
    """Repository for managing model inference event logs."""

    def __init__(self, db: Session):
        self.db = db

    def create_prediction_log(
        self,
        transaction_id: str,
        model_name: str,
        model_version: str,
        probability: float,
        prediction: int,
        risk_score: float,
        risk_level: str,
        threshold_used: float
    ) -> PredictionModel:
        """Create new prediction log event."""
        pred_obj = PredictionModel(
            transaction_id=transaction_id,
            model_name=model_name,
            model_version=model_version,
            fraud_probability=probability,
            fraud_prediction=prediction,
            risk_score=risk_score,
            risk_level=risk_level,
            threshold_used=threshold_used,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(pred_obj)
        self.db.commit()
        self.db.refresh(pred_obj)
        return pred_obj

    def count(self) -> int:
        """Count total stored prediction logs."""
        return self.db.query(func.count(PredictionModel.id)).scalar() or 0


class AlertRepository:
    """Repository for managing security alerts queue."""

    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        transaction_id: str,
        severity: str,
        fraud_probability: float,
        risk_score: float,
        message: str,
        alert_type: str = "FRAUD_RISK_FLAG"
    ) -> Optional[AlertModel]:
        """
        Creates alert for transaction if no open alert currently exists.
        Prevents duplicate active alerts.
        """
        existing_open = (
            self.db.query(AlertModel)
            .filter(
                AlertModel.transaction_id == transaction_id,
                AlertModel.status.in_(["OPEN", "INVESTIGATING"])
            )
            .first()
        )

        if existing_open:
            logger.info(f"Open alert already exists for transaction {transaction_id}. Skipping duplicate alert.")
            return existing_open

        alert_obj = AlertModel(
            transaction_id=transaction_id,
            alert_type=alert_type,
            severity=severity,
            fraud_probability=fraud_probability,
            risk_score=risk_score,
            status="OPEN",
            message=message,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(alert_obj)
        self.db.commit()
        self.db.refresh(alert_obj)
        logger.info(f"Triggered {severity} risk alert (ID: {alert_obj.id}) for transaction {transaction_id}.")
        return alert_obj

    def get_all_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AlertModel]:
        """Fetch paginated alert queue."""
        query = self.db.query(AlertModel)
        if status:
            query = query.filter(AlertModel.status == status.upper())
        if severity:
            query = query.filter(AlertModel.severity == severity.upper())

        return query.order_by(desc(AlertModel.id)).offset(skip).limit(limit).all()

    def count(self, status: Optional[str] = None, severity: Optional[str] = None) -> int:
        """Count alert notifications."""
        query = self.db.query(func.count(AlertModel.id))
        if status:
            query = query.filter(AlertModel.status == status.upper())
        if severity:
            query = query.filter(AlertModel.severity == severity.upper())
        return query.scalar() or 0

    def get_by_id(self, alert_id: int) -> Optional[AlertModel]:
        """Find alert by primary ID."""
        return self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    def update_status(self, alert_id: int, new_status: str, notes: Optional[str] = None) -> Optional[AlertModel]:
        """Update alert status (INVESTIGATING, RESOLVED, DISMISSED) and record notes."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        valid_statuses = ["OPEN", "INVESTIGATING", "RESOLVED", "DISMISSED"]
        norm_status = new_status.upper()
        if norm_status not in valid_statuses:
            raise ValueError(f"Invalid alert status: '{new_status}'. Allowed statuses: {valid_statuses}")

        alert.status = norm_status
        if notes:
            alert.resolution_notes = notes

        if norm_status in ["RESOLVED", "DISMISSED"]:
            alert.resolved_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(alert)
        logger.info(f"Updated alert #{alert_id} status to {norm_status}")
        return alert
