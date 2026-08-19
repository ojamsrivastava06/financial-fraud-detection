"""
Unit tests for transaction streaming simulation and FraudMonitor service.
"""

import pytest
from src.monitoring.transaction_stream import generate_transaction_stream
from src.monitoring.fraud_monitor import FraudMonitor
from src.database.connection import SessionLocal


def test_generate_transaction_stream():
    """Verify transaction stream generator yields valid transaction payloads."""
    stream = generate_transaction_stream(batch_size=5, delay_seconds=0.0)
    events = list(stream)

    assert len(events) == 5
    assert "transaction_id" in events[0]
    assert "transaction_amount" in events[0]


def test_fraud_monitor_process_transaction():
    """Verify FraudMonitor processes single stream event through prediction & database."""
    db = SessionLocal()
    try:
        sample_event = {
            "transaction_id": "STREAM_TEST_001",
            "customer_id": "CUST_STREAM_001",
            "transaction_date": "14-08-2026 15:00",
            "transaction_amount": 600.0,
            "merchant_category": "Travel",
            "payment_method": "Credit Card",
            "device_type": "POS",
            "location": "Bengaluru",
            "is_international": 1,
            "previous_transactions": 2,
            "average_spend": 25.0,
            "account_age_days": 30,
            "suspicious_keyword": "Yes"
        }

        monitor = FraudMonitor(db)
        result = monitor.process_transaction(sample_event, db=db)

        assert result.get("status") != "error"
        assert result["transaction_id"] == "STREAM_TEST_001"
        assert 0.0 <= result["fraud_probability"] <= 1.0
        assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    finally:
        db.close()


def test_fraud_monitor_handles_invalid_payload():
    """Verify FraudMonitor handles malformed transaction payloads safely without crashing."""
    db = SessionLocal()
    try:
        invalid_event = {"invalid_key": "bad_value"}
        monitor = FraudMonitor(db)
        result = monitor.process_transaction(invalid_event, db=db)

        assert result["status"] in ["error", "model_not_loaded"]
    finally:
        db.close()
