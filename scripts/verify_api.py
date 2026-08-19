"""
Live endpoint verification script for Financial Fraud Detection API.
Directly exercises each required endpoint and asserts response structure and HTTP status codes.
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

SAMPLE_PREDICT = {
    "transaction": {
        "transaction_id": "T_AUDIT_001",
        "customer_id": "CUST_AUDIT_01",
        "transaction_date": "16-08-2026 19:30",
        "transaction_amount": 750.0,
        "merchant_category": "Travel",
        "payment_method": "Credit Card",
        "device_type": "POS",
        "location": "Bengaluru",
        "is_international": 1,
        "previous_transactions": 2,
        "average_spend": 50.0,
        "account_age_days": 30,
        "suspicious_keyword": "Yes"
    }
}

SAMPLE_BATCH = {
    "transactions": [
        {
            "transaction_id": "T_AUDIT_BATCH_1",
            "customer_id": "CUST_AUDIT_B1",
            "transaction_date": "16-08-2026 19:30",
            "transaction_amount": 25.0,
            "merchant_category": "Grocery",
            "payment_method": "Debit Card",
            "device_type": "Mobile",
            "location": "Mumbai",
            "is_international": 0,
            "previous_transactions": 100,
            "average_spend": 30.0,
            "account_age_days": 400,
            "suspicious_keyword": "No"
        },
        {
            "transaction_id": "T_AUDIT_BATCH_2",
            "customer_id": "CUST_AUDIT_B2",
            "transaction_date": "16-08-2026 19:30",
            "transaction_amount": 1200.0,
            "merchant_category": "Travel",
            "payment_method": "Credit Card",
            "device_type": "POS",
            "location": "Bengaluru",
            "is_international": 1,
            "previous_transactions": 1,
            "average_spend": 40.0,
            "account_age_days": 10,
            "suspicious_keyword": "Yes"
        }
    ]
}


def verify_endpoints():
    print("=" * 70)
    print("API ENDPOINT VERIFICATION")
    print("=" * 70)

    # 1. GET /health
    r_health = client.get("/health")
    print(f"\n1. GET /health -> Status: {r_health.status_code}")
    print(f"   Payload: {json.dumps(r_health.json(), indent=2)}")
    assert r_health.status_code == 200, f"GET /health failed: {r_health.status_code}"
    assert r_health.json()["status"] == "healthy"

    # 2. GET /ready
    r_ready = client.get("/ready")
    print(f"\n2. GET /ready -> Status: {r_ready.status_code}")
    print(f"   Payload: {json.dumps(r_ready.json(), indent=2)}")
    assert r_ready.status_code == 200, f"GET /ready failed: {r_ready.status_code}"
    assert r_ready.json()["status"] == "ready"

    # 3. GET /transactions
    r_tx = client.get("/transactions?limit=2")
    print(f"\n3. GET /transactions?limit=2 -> Status: {r_tx.status_code}")
    print(f"   Count returned: {len(r_tx.json())}")
    print(f"   Sample item: {json.dumps(r_tx.json()[0] if r_tx.json() else {}, indent=2)}")
    assert r_tx.status_code == 200, f"GET /transactions failed: {r_tx.status_code}"
    assert len(r_tx.json()) > 0

    # 4. GET /analytics/summary
    r_summary = client.get("/analytics/summary")
    print(f"\n4. GET /analytics/summary -> Status: {r_summary.status_code}")
    print(f"   Payload: {json.dumps(r_summary.json(), indent=2)}")
    assert r_summary.status_code == 200, f"GET /analytics/summary failed: {r_summary.status_code}"
    assert r_summary.json()["total_transactions"] >= 5000

    # 5. GET /alerts
    r_alerts = client.get("/alerts?limit=2")
    print(f"\n5. GET /alerts?limit=2 -> Status: {r_alerts.status_code}")
    print(f"   Count returned: {len(r_alerts.json())}")
    print(f"   Sample item: {json.dumps(r_alerts.json()[0] if r_alerts.json() else {}, indent=2)}")
    assert r_alerts.status_code == 200, f"GET /alerts failed: {r_alerts.status_code}"

    # 6. POST /predictions/predict
    r_predict = client.post("/predictions/predict", json=SAMPLE_PREDICT)
    print(f"\n6. POST /predictions/predict -> Status: {r_predict.status_code}")
    print(f"   Payload: {json.dumps(r_predict.json(), indent=2)}")
    assert r_predict.status_code == 200, f"POST /predictions/predict failed: {r_predict.status_code}"
    assert "fraud_probability" in r_predict.json()

    # 7. POST /predictions/batch
    r_batch = client.post("/predictions/batch", json=SAMPLE_BATCH)
    print(f"\n7. POST /predictions/batch -> Status: {r_batch.status_code}")
    print(f"   Payload: {json.dumps(r_batch.json(), indent=2)}")
    assert r_batch.status_code == 200, f"POST /predictions/batch failed: {r_batch.status_code}"
    assert r_batch.json()["total_submitted"] == 2
    assert r_batch.json()["successful_predictions"] == 2

    print("\n" + "=" * 70)
    print("ALL 7 API ENDPOINTS VERIFIED AND WORKING PERFECTLY.")
    print("=" * 70)

    # Clean up test transactions to keep the database in a pristine 5000-record state
    from scripts.cleanup_database import cleanup_test_records
    cleanup_test_records()


if __name__ == "__main__":
    verify_endpoints()
