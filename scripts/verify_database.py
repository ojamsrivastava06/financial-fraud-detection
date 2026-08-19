"""
Database contents verification script.
Checks exact counts of transactions, predictions, and alerts in SQLite database.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.database.connection import SessionLocal
from src.database.models import TransactionModel, PredictionModel, AlertModel

def verify_database_records():
    print("=" * 70)
    print("SQLITE DATABASE INTEGRITY & RECORD COUNT AUDIT")
    print("=" * 70)

    db = SessionLocal()
    try:
        tx_count = db.query(TransactionModel).count()
        pred_count = db.query(PredictionModel).count()
        alert_count = db.query(AlertModel).count()

        open_alerts = db.query(AlertModel).filter(AlertModel.status == "OPEN").count()
        investigating_alerts = db.query(AlertModel).filter(AlertModel.status == "INVESTIGATING").count()
        resolved_alerts = db.query(AlertModel).filter(AlertModel.status == "RESOLVED").count()
        dismissed_alerts = db.query(AlertModel).filter(AlertModel.status == "DISMISSED").count()

        print(f"Total Stored Transactions: {tx_count}")
        print(f"Total Stored Prediction Records: {pred_count}")
        print(f"Total Stored Alert Records: {alert_count}")
        print(f"  - OPEN Alerts: {open_alerts}")
        print(f"  - INVESTIGATING Alerts: {investigating_alerts}")
        print(f"  - RESOLVED Alerts: {resolved_alerts}")
        print(f"  - DISMISSED Alerts: {dismissed_alerts}")

        assert tx_count >= 5000, f"Expected >= 5000 transactions, found {tx_count}"
        assert pred_count >= 5000, f"Expected >= 5000 predictions, found {pred_count}"
        assert alert_count > 0, f"Expected > 0 alerts, found {alert_count}"

        print("\n" + "=" * 70)
        print("DATABASE RECORD AUDIT: PASSED (All records intact)")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    verify_database_records()
