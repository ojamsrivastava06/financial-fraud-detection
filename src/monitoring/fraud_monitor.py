"""
Real-time fraud monitor service.
Consumes transaction events, executes feature pipeline & model inference,
persists predictions to database, and triggers security alert engine.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.repository import TransactionRepository, PredictionRepository
from src.models.predict import predict_fraud_probability
from src.monitoring.alert_engine import AlertEngine
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FraudMonitor:
    """Monitors incoming transaction streams and executes real-time risk scoring."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def process_transaction(
        self,
        transaction_payload: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Process single transaction event through prediction engine, database, and alert pipeline.

        Returns:
            Dict containing prediction details and alert status.
        """
        session = db or self.db or SessionLocal()
        close_session = (db is None and self.db is None)

        try:
            # 1. Run ML model inference
            pred_result = predict_fraud_probability(transaction_payload)
            if pred_result.get("status") == "model_not_loaded":
                logger.warning("FraudMonitor prediction skipped: Model not loaded.")
                return pred_result

            tx_id = transaction_payload.get("transaction_id", "UNKNOWN")
            prob = pred_result["fraud_probability"]
            risk_score = pred_result["risk_score"]
            risk_level = pred_result["risk_level"]
            pred_flag = pred_result["fraud_prediction"]
            threshold = pred_result.get("operating_threshold", 0.65)

            # 2. Persist Transaction & Prediction Log to DB
            tx_repo = TransactionRepository(session)
            pred_repo = PredictionRepository(session)

            pred_info = {
                "fraud_probability": prob,
                "fraud_prediction": pred_flag,
                "risk_score": risk_score,
                "risk_level": risk_level
            }

            tx_repo.create_or_update(transaction_payload, pred_info)

            pred_repo.create_prediction_log(
                transaction_id=tx_id,
                model_name=pred_result.get("model_name", "LogisticRegression"),
                model_version="1.0.0",
                probability=prob,
                prediction=pred_flag,
                risk_score=risk_score,
                risk_level=risk_level,
                threshold_used=threshold
            )

            # 3. Trigger Alert Engine
            alert_engine = AlertEngine(session)
            alert_obj = alert_engine.evaluate_and_trigger_alert(
                transaction_id=tx_id,
                risk_level=risk_level,
                probability=prob,
                risk_score=risk_score,
                db=session
            )

            pred_result["alert_id"] = alert_obj.id if alert_obj else None
            pred_result["alert_created"] = alert_obj is not None

            logger.info(f"FraudMonitor processed TX '{tx_id}': Prob={prob:.4f}, Risk={risk_level}")
            return pred_result

        except Exception as e:
            logger.error(f"Error processing transaction in FraudMonitor: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Transaction processing failure: {str(e)}"
            }
        finally:
            if close_session:
                session.close()
