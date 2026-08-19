"""
Database Seeding Script.
Loads raw dataset (5,000 transactions), executes preprocessing and trained ML model inference,
calculates risk scores, stores transactions & prediction records in SQLite DB, and triggers alert engine.
Uses bulk session commits for high-performance idempotent seeding.
"""

from pathlib import Path
import sys
from datetime import datetime, timezone

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.database.connection import init_db, SessionLocal
from src.database.models import TransactionModel, PredictionModel, AlertModel
from src.data.ingestion import load_raw_dataset
from src.features.engineering import build_features
from src.models.model_registry import ModelRegistry
from src.models.risk_scoring import calculate_risk_score
from src.utils.logger import get_logger

logger = get_logger(__name__)


def seed_database():
    """Initializes SQLite tables and populates with 5,000 processed transaction records."""
    logger.info("==================================================")
    logger.info("STARTING HIGH-PERFORMANCE DATABASE SEEDING")
    logger.info("==================================================")

    # 1. Initialize DB tables with fresh schema
    init_db(drop_existing=True)
    db = SessionLocal()

    # 2. Load Model Artifacts from Registry
    registry = ModelRegistry()
    model, preprocessor, metadata = registry.load_active_model()

    if model is None or preprocessor is None or metadata is None:
        logger.error("Model artifacts not found! Run python scripts/train_model.py first.")
        sys.exit(1)

    model_name = metadata.get("model_name", "LogisticRegression")
    model_version = metadata.get("model_version", "1.0.0")
    selected_threshold = metadata.get("selected_threshold", 0.65)
    risk_thresholds = metadata.get("risk_thresholds", {"low_risk": 0.35, "medium_risk": 0.35, "high_risk": 0.65})
    high_th = risk_thresholds.get("high_risk", 0.65)
    med_th = risk_thresholds.get("medium_risk", 0.35)

    # 3. Load Raw Dataset
    df_raw = load_raw_dataset()
    logger.info(f"Loaded raw dataset for seeding: {len(df_raw)} records.")

    # 4. Feature Engineering
    df_engineered, _ = build_features(df_raw)

    # 5. Preprocess Features using Fitted Preprocessor
    drop_cols = ["Transaction_ID", "Customer_ID", "Transaction_Date", "Suspicious_Keyword", "Is_International", "Fraudulent"]
    feature_cols = [c for c in df_engineered.columns if c not in drop_cols]
    X_features = df_engineered[feature_cols]

    X_transformed = preprocessor.transform(X_features)
    probabilities = model.predict_proba(X_transformed)[:, 1]

    tx_objects = []
    pred_objects = []
    alert_objects = []

    alerts_triggered = 0

    for idx, row in df_raw.iterrows():
        tx_id = str(row["Transaction_ID"])
        prob = float(probabilities[idx])

        # Risk scoring
        risk_info = calculate_risk_score(
            probability=prob,
            high_risk_threshold=high_th,
            medium_risk_threshold=med_th
        )

        pred_flag = int(prob >= selected_threshold)
        risk_score = risk_info["risk_score"]
        risk_level = risk_info["risk_level"]

        tx_obj = TransactionModel(
            transaction_id=tx_id,
            customer_id=str(row["Customer_ID"]),
            transaction_date=str(row["Transaction_Date"]),
            transaction_amount=float(row["Transaction_Amount"]),
            merchant_category=str(row["Merchant_Category"]),
            payment_method=str(row["Payment_Method"]),
            device_type=str(row["Device_Type"]),
            location=str(row["Location"]),
            is_international=int(row["Is_International"]),
            previous_transactions=int(row["Previous_Transactions"]),
            average_spend=float(row["Average_Spend"]),
            account_age_days=int(row["Account_Age_Days"]),
            suspicious_keyword=str(row["Suspicious_Keyword"]),
            fraudulent=int(row["Fraudulent"]),
            fraud_probability=round(prob, 4),
            fraud_prediction=pred_flag,
            risk_score=risk_score,
            risk_level=risk_level,
            prediction_timestamp=datetime.now(timezone.utc)
        )
        tx_objects.append(tx_obj)

        pred_obj = PredictionModel(
            transaction_id=tx_id,
            model_name=model_name,
            model_version=model_version,
            fraud_probability=round(prob, 4),
            fraud_prediction=pred_flag,
            risk_score=risk_score,
            risk_level=risk_level,
            threshold_used=selected_threshold,
            created_at=datetime.now(timezone.utc)
        )
        pred_objects.append(pred_obj)

        if risk_level in ["HIGH", "MEDIUM"]:
            severity = "CRITICAL" if prob >= 0.85 else ("HIGH" if risk_level == "HIGH" else "MEDIUM")
            msg = f"{risk_level.title()}-risk transaction detected: {prob * 100:.1f}% fraud probability."
            alert_obj = AlertModel(
                transaction_id=tx_id,
                alert_type="FRAUD_RISK_FLAG",
                severity=severity,
                fraud_probability=round(prob, 4),
                risk_score=risk_score,
                status="OPEN",
                message=msg,
                created_at=datetime.now(timezone.utc)
            )
            alert_objects.append(alert_obj)
            alerts_triggered += 1

    # Bulk add and commit in one transaction
    logger.info("Executing bulk database insert for transactions, predictions, and alerts...")
    db.bulk_save_objects(tx_objects)
    db.bulk_save_objects(pred_objects)
    db.bulk_save_objects(alert_objects)
    db.commit()
    db.close()

    logger.info(f"Database seeding complete. Seeded {len(tx_objects)} transactions & {len(pred_objects)} predictions.")
    logger.info(f"Triggered {alerts_triggered} security alerts during seeding.")
    logger.info("==================================================")


if __name__ == "__main__":
    seed_database()
