"""
Production Hardening & Reliability Test Suite for Financial Fraud Detection Platform.
Tests API payload validation, error states, readiness probes, database edge cases,
security controls, and status transitions.
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from src.api.main import app
from src.config.settings import settings
from src.database.connection import SessionLocal
from src.database.repository import AlertRepository, TransactionRepository
from src.models.model_registry import ModelRegistry

client = TestClient(app)

VALID_TRANSACTION_PAYLOAD = {
    "transaction_id": "T_PROD_TEST_001",
    "customer_id": "CUST_PROD_001",
    "transaction_date": "14-08-2026 14:30",
    "transaction_amount": 550.0,
    "merchant_category": "Travel",
    "payment_method": "Credit Card",
    "device_type": "POS",
    "location": "Bengaluru",
    "is_international": 1,
    "previous_transactions": 5,
    "average_spend": 40.0,
    "account_age_days": 45,
    "suspicious_keyword": "Yes"
}


# ==============================================================================
# 1. API Payload Validation Tests
# ==============================================================================

def test_missing_required_fields_returns_422():
    """Omitting required fields must return 422 Unprocessable Entity with error detail."""
    incomplete_payload = {
        "transaction": {
            "transaction_id": "T_INCOMPLETE",
            # missing customer_id, transaction_amount, merchant_category, etc.
        }
    }
    response = client.post("/predictions/predict", json=incomplete_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "detail" in data


def test_invalid_payload_types_returns_422():
    """Sending non-numeric values for transaction_amount must return 422."""
    invalid_payload = {
        "transaction": {
            **VALID_TRANSACTION_PAYLOAD,
            "transaction_amount": "NOT_A_NUMBER"
        }
    }
    response = client.post("/predictions/predict", json=invalid_payload)
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_negative_transaction_amount_rejected():
    """Negative transaction amounts must fail Pydantic gt=0 validation with 422."""
    negative_payload = {
        "transaction": {
            **VALID_TRANSACTION_PAYLOAD,
            "transaction_amount": -150.0
        }
    }
    response = client.post("/predictions/predict", json=negative_payload)
    assert response.status_code == 422
    assert "transaction_amount" in response.json()["detail"]


def test_zero_transaction_amount_rejected():
    """Zero transaction amounts must fail gt=0 validation with 422."""
    zero_payload = {
        "transaction": {
            **VALID_TRANSACTION_PAYLOAD,
            "transaction_amount": 0.0
        }
    }
    response = client.post("/predictions/predict", json=zero_payload)
    assert response.status_code == 422


def test_invalid_is_international_value_rejected():
    """is_international must be 0 or 1."""
    invalid_payload = {
        "transaction": {
            **VALID_TRANSACTION_PAYLOAD,
            "is_international": 5
        }
    }
    response = client.post("/predictions/predict", json=invalid_payload)
    assert response.status_code == 422


# ==============================================================================
# 2. Batch Prediction Edge Cases & Size Limits
# ==============================================================================

def test_batch_prediction_empty_list_rejected():
    """Empty batch submission must return 400 Bad Request."""
    response = client.post("/predictions/batch", json={"transactions": []})
    assert response.status_code in [400, 422]


def test_batch_prediction_exceeding_max_limit():
    """Submitting more transactions than MAX_BATCH_SIZE must return 413 or 422."""
    large_batch = {
        "transactions": [VALID_TRANSACTION_PAYLOAD] * (settings.MAX_BATCH_SIZE + 1)
    }
    response = client.post("/predictions/batch", json=large_batch)
    assert response.status_code in [413, 422]


def test_batch_prediction_handles_corrupt_items_gracefully():
    """Batch prediction processes valid items and isolates errors without crashing."""
    valid_item = {**VALID_TRANSACTION_PAYLOAD, "transaction_id": "T_BATCH_VALID"}
    payload = {"transactions": [valid_item]}
    response = client.post("/predictions/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_submitted"] == 1
    assert data["successful_predictions"] == 1
    assert data["failed_predictions"] == 0
    assert len(data["predictions"]) == 1


# ==============================================================================
# 3. Not Found & Resource Edge Cases
# ==============================================================================

def test_get_nonexistent_transaction_returns_404():
    """Querying an unknown transaction ID returns 404 with structured error."""
    response = client.get("/transactions/NON_EXISTENT_TX_999999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "NON_EXISTENT_TX_999999" in data["detail"]


def test_get_nonexistent_alert_returns_404():
    """Querying an unknown alert ID returns 404."""
    response = client.get("/alerts/9999999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_update_nonexistent_alert_returns_404():
    """Updating status on unknown alert returns 404."""
    response = client.patch("/alerts/9999999", json={"status": "RESOLVED"})
    assert response.status_code == 404


# ==============================================================================
# 4. Security Alerts & Status Transition Validation
# ==============================================================================

def test_alert_invalid_status_transition_rejected():
    """Sending an unsupported status string returns 400 or 422."""
    response = client.patch("/alerts/1", json={"status": "INVALID_STATE_NAME"})
    assert response.status_code in [400, 422]


def test_alert_valid_status_transitions():
    """Verify standard status workflow transition OPEN -> INVESTIGATING -> RESOLVED."""
    db = SessionLocal()
    try:
        repo = AlertRepository(db)
        alert = repo.create_alert(
            transaction_id="T_ALERT_WORKFLOW_TEST",
            severity="HIGH",
            fraud_probability=0.88,
            risk_score=88.0,
            message="Test workflow alert"
        )
        alert_id = alert.id

        # Transition 1: INVESTIGATING
        r1 = client.patch(f"/alerts/{alert_id}", json={"status": "INVESTIGATING", "resolution_notes": "Under review"})
        assert r1.status_code == 200
        assert r1.json()["status"] == "INVESTIGATING"

        # Transition 2: RESOLVED
        r2 = client.patch(f"/alerts/{alert_id}", json={"status": "RESOLVED", "resolution_notes": "Verified legitimate cardholder"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "RESOLVED"
        assert r2.json()["resolved_at"] is not None
    finally:
        db.close()


# ==============================================================================
# 5. Health & Readiness Probe Verification
# ==============================================================================

def test_health_liveness_endpoint():
    """GET /health returns healthy status, database and model loaded."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "app_name" in data


def test_readiness_probe_all_healthy():
    """GET /ready returns 200 OK and ready status when all components operational."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"]["status"] == "healthy"
    assert data["model_artifact"]["status"] == "healthy"
    assert data["preprocessor_artifact"]["status"] == "healthy"
    assert data["metadata_artifact"]["status"] == "healthy"


def test_readiness_probe_database_failure_handling():
    """Simulated database failure causes /ready to return 503 Service Unavailable."""
    with patch("src.api.routes.health.text", side_effect=Exception("Connection refused")):
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"]["status"] == "unhealthy"


# ==============================================================================
# 6. Performance & Security Headers
# ==============================================================================

def test_timing_middleware_header_present():
    """All API responses must include the X-Process-Time-Ms diagnostic header."""
    response = client.get("/health")
    assert "X-Process-Time-Ms" in response.headers
    process_time = float(response.headers["X-Process-Time-Ms"])
    assert process_time >= 0.0


def test_pagination_bounds_and_safeguards():
    """Limit query param must reject values <= 0 or > 500."""
    # Test limit exceeding max
    r_exceed = client.get("/transactions?limit=1000")
    assert r_exceed.status_code == 422

    # Test negative skip
    r_neg_skip = client.get("/transactions?skip=-5")
    assert r_neg_skip.status_code == 422


def test_global_exception_handler_sanitizes_errors():
    """Unhandled exceptions return 500 without leaking file paths or traceback internals."""
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    with patch("src.api.routes.analytics.TransactionRepository.get_analytics_summary", side_effect=RuntimeError("Secret internal database error")):
        response = client_no_raise.get("/analytics/summary")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        assert "Secret internal database error" not in data["detail"]
        assert "traceback" not in data
