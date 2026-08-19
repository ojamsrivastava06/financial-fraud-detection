"""
Unit tests for FastAPI REST API endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /health returns 200 OK with system status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] == "connected"
    assert data["model_loaded"] is True


def test_root_endpoint():
    """Verify GET / returns 200 OK with landing endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "health_check" in data


def test_get_transactions_list():
    """Verify GET /transactions returns paginated transactions."""
    response = client.get("/transactions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    if data:
        assert "transaction_id" in data[0]


def test_get_transaction_by_id():
    """Verify GET /transactions/{id} returns specific transaction."""
    response = client.get("/transactions/T100000")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "T100000"


def test_predict_single_transaction_endpoint():
    """Verify POST /predictions/predict returns structured prediction."""
    payload = {
        "transaction": {
            "transaction_id": "T99999_API_TEST",
            "customer_id": "CUST_API_TEST",
            "transaction_date": "14-08-2026 14:30",
            "transaction_amount": 500.0,
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
    }
    response = client.post("/predictions/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "T99999_API_TEST"
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]


def test_batch_prediction_endpoint():
    """Verify POST /predictions/batch returns predictions for list of transactions."""
    payload = {
        "transactions": [
            {
                "transaction_id": "T88881",
                "customer_id": "CUST881",
                "transaction_date": "14-08-2026 10:00",
                "transaction_amount": 30.0,
                "merchant_category": "Grocery",
                "payment_method": "Debit Card",
                "device_type": "Mobile",
                "location": "Mumbai",
                "is_international": 0,
                "previous_transactions": 100,
                "average_spend": 35.0,
                "account_age_days": 500,
                "suspicious_keyword": "No"
            }
        ]
    }
    response = client.post("/predictions/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_submitted"] == 1
    assert data["successful_predictions"] == 1


def test_analytics_summary_endpoint():
    """Verify GET /analytics/summary returns calculated database metrics."""
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] >= 5000
    assert "fraud_rate_pct" in data


def test_analytics_time_series_endpoint():
    """Verify GET /analytics/time-series returns daily trend data."""
    response = client.get("/analytics/time-series")
    assert response.status_code == 200
    data = response.json()
    assert "data_points" in data


def test_alerts_endpoints():
    """Verify GET /alerts, GET /alerts/{id}, and PATCH /alerts/{id}."""
    # List alerts
    response = client.get("/alerts?limit=5")
    assert response.status_code == 200
    alerts_data = response.json()
    assert isinstance(alerts_data, list)

    if alerts_data:
        alert_id = alerts_data[0]["id"]
        # Detail lookup
        detail_resp = client.get(f"/alerts/{alert_id}")
        assert detail_resp.status_code == 200

        # Patch update
        patch_payload = {"status": "INVESTIGATING", "resolution_notes": "Assigned to test team."}
        patch_resp = client.patch(f"/alerts/{alert_id}", json=patch_payload)
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "INVESTIGATING"
