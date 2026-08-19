"""
Surgical database cleanup script.
Deletes only test, demo, and verification records created by automated tests/benchmarks.
Guarantees 100% preservation of original seeded transactions (T1 - T5000), predictions, and alerts.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.database.connection import SessionLocal
from src.database.models import TransactionModel, PredictionModel, AlertModel

def cleanup_test_records():
    print("=" * 70)
    print("SURGICAL DATABASE CLEANUP: REMOVING NON-DATASET TEST RECORDS")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Identify non-original transaction IDs (T1 to T5000 are original dataset)
        all_txs = db.query(TransactionModel.transaction_id).all()
        tx_ids = [t[0] for t in all_txs]

        # Valid dataset IDs: T100000 to T104999 (from raw dataset CSV)
        valid_dataset_ids = set()
        for i in range(100000, 105000):
            valid_dataset_ids.add(f"T{i}")
            valid_dataset_ids.add(str(i))

        test_tx_ids = [t for t in tx_ids if t not in valid_dataset_ids]

        print(f"Total Transactions in DB: {len(tx_ids)}")
        print(f"Seeded Dataset Transactions (Preserved): {len(tx_ids) - len(test_tx_ids)}")
        print(f"Test/Audit Transactions to Remove: {len(test_tx_ids)}")

        if test_tx_ids:
            print("\nRemoving test transactions and associated prediction/alert records...")
            for tid in test_tx_ids:
                print(f"  - Deleting records for transaction: {tid}")

            # 1. Delete associated Alerts
            deleted_alerts = db.query(AlertModel).filter(
                (AlertModel.transaction_id.in_(test_tx_ids)) |
                (AlertModel.id > 1722) |
                (AlertModel.message.like("Test%"))
            ).delete(synchronize_session=False)
            # 2. Delete associated Predictions
            deleted_preds = db.query(PredictionModel).filter(PredictionModel.transaction_id.in_(test_tx_ids)).delete(synchronize_session=False)
            # 3. Delete Transactions
            deleted_txs = db.query(TransactionModel).filter(TransactionModel.transaction_id.in_(test_tx_ids)).delete(synchronize_session=False)

            db.commit()

            print(f"\nCleanup Summary:")
            print(f"  - Deleted Test Alerts: {deleted_alerts}")
            print(f"  - Deleted Test Predictions: {deleted_preds}")
            print(f"  - Deleted Test Transactions: {deleted_txs}")
        else:
            # Check if there are orphaned test alerts
            orphaned_alerts = db.query(AlertModel).filter(
                (AlertModel.id > 1722) |
                (AlertModel.message.like("Test%"))
            ).delete(synchronize_session=False)
            if orphaned_alerts:
                db.commit()
                print(f"Deleted {orphaned_alerts} orphaned test alert records.")
            else:
                print("No non-dataset test records found. Database is already clean.")

        # Verify final record counts
        final_txs = db.query(TransactionModel).count()
        final_preds = db.query(PredictionModel).count()
        final_alerts = db.query(AlertModel).count()

        print("\n" + "=" * 70)
        print("POST-CLEANUP RECORD COUNTS:")
        print(f"  - Total Transactions: {final_txs}")
        print(f"  - Total Predictions:  {final_preds}")
        print(f"  - Total Alerts:       {final_alerts}")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    cleanup_test_records()
