"""
Unit tests for database initialization, transaction insertion, predictions, alerts, and analytics queries.
"""

import pytest
from src.database.connection import SessionLocal, init_db
from src.database.repository import TransactionRepository, PredictionRepository, AlertRepository
from src.database.models import TransactionModel, AlertModel


def test_database_initialization():
    """Verify database schema creation succeeds without error."""
    init_db(drop_existing=False)
    db = SessionLocal()
    try:
        tx_repo = TransactionRepository(db)
        assert tx_repo.count() > 0
    finally:
        db.close()


def test_transaction_repository_queries():
    """Test transaction repository queries, filtering, and summary calculations."""
    db = SessionLocal()
    try:
        tx_repo = TransactionRepository(db)
        total_tx = tx_repo.count()
        assert total_tx >= 5000

        # Filter high risk
        high_risk_tx = tx_repo.get_all(risk_level="HIGH", limit=10)
        assert isinstance(high_risk_tx, list)

        # Analytics summary
        summary = tx_repo.get_analytics_summary()
        assert summary["total_transactions"] >= 5000
        assert summary["fraud_rate_pct"] > 0.0

        # Time series analytics
        ts = tx_repo.get_time_series_analytics()
        assert isinstance(ts, list)
        assert len(ts) > 0
    finally:
        db.close()


def test_alert_repository_workflow():
    """Test creating an alert, querying alerts, and updating status."""
    db = SessionLocal()
    try:
        alert_repo = AlertRepository(db)
        test_tx_id = "T100000"

        # Create alert
        alert = alert_repo.create_alert(
            transaction_id=test_tx_id,
            severity="HIGH",
            fraud_probability=0.88,
            risk_score=88.0,
            message="Test high-risk alert"
        )
        assert alert is not None
        assert alert.transaction_id == test_tx_id

        # Update status
        updated = alert_repo.update_status(alert.id, "INVESTIGATING", "Analyst assigned.")
        assert updated.status == "INVESTIGATING"

        resolved = alert_repo.update_status(alert.id, "RESOLVED", "Cardholder confirmed purchase.")
        assert resolved.status == "RESOLVED"
        assert resolved.resolved_at is not None
    finally:
        db.close()
