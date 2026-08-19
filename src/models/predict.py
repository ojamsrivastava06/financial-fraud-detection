"""
Prediction engine module providing real-time inference interface for transactions.
"""

from typing import Dict, Any, Union, Optional
import pandas as pd
import numpy as np
from src.features.engineering import build_features
from src.models.risk_scoring import calculate_risk_score
from src.models.model_registry import ModelRegistry
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Column name mapping between Pydantic snake_case and raw CSV Title_Case
COLUMN_NAME_MAPPING = {
    "transaction_id": "Transaction_ID",
    "customer_id": "Customer_ID",
    "transaction_date": "Transaction_Date",
    "transaction_amount": "Transaction_Amount",
    "merchant_category": "Merchant_Category",
    "payment_method": "Payment_Method",
    "device_type": "Device_Type",
    "location": "Location",
    "is_international": "Is_International",
    "previous_transactions": "Previous_Transactions",
    "average_spend": "Average_Spend",
    "account_age_days": "Account_Age_Days",
    "suspicious_keyword": "Suspicious_Keyword",
    "fraudulent": "Fraudulent"
}


def normalize_input_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize input column names to standard raw dataset format."""
    df_norm = df.copy()
    rename_dict = {}
    for col in df_norm.columns:
        col_lower = col.lower()
        if col_lower in COLUMN_NAME_MAPPING:
            rename_dict[col] = COLUMN_NAME_MAPPING[col_lower]
    if rename_dict:
        df_norm = df_norm.rename(columns=rename_dict)
    return df_norm


def predict_fraud_probability(
    transaction_data: Union[Dict[str, Any], pd.DataFrame],
    model: Optional[Any] = None,
    preprocessor: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes fraud probability, risk score, and risk tier for transaction payload.

    Args:
        transaction_data: Transaction dictionary or pandas DataFrame.
        model: Trained classifier instance (loaded from ModelRegistry if None).
        preprocessor: Fitted ColumnTransformer instance (loaded from ModelRegistry if None).
        metadata: Model metadata dict (loaded from ModelRegistry if None).

    Returns:
        Dict containing fraud_probability, fraud_percentage, fraud_prediction, risk_score, and risk_level.
    """
    # Load model and preprocessor if not explicitly passed
    if model is None or preprocessor is None or metadata is None:
        registry = ModelRegistry()
        reg_model, reg_preproc, reg_meta = registry.load_active_model()
        model = model or reg_model
        preprocessor = preprocessor or reg_preproc
        metadata = metadata or reg_meta

    if model is None or preprocessor is None:
        logger.warning("Prediction requested but trained model/preprocessor is not available in registry.")
        return {
            "status": "model_not_loaded",
            "fraud_probability": None,
            "fraud_percentage": None,
            "fraud_prediction": None,
            "risk_score": None,
            "risk_level": "UNKNOWN",
            "message": "Trained model artifacts not found. Please run model training pipeline first."
        }

    # Convert dictionary to DataFrame if needed
    if isinstance(transaction_data, dict):
        df_input = pd.DataFrame([transaction_data])
    else:
        df_input = transaction_data.copy()

    # Step 0: Normalize column names (handles snake_case from Pydantic schemas)
    df_input = normalize_input_columns(df_input)

    # Step 1: Feature Engineering
    df_engineered, _ = build_features(df_input)

    # Step 2: Select expected raw + engineered features for ColumnTransformer
    drop_cols = ["Transaction_ID", "Customer_ID", "Transaction_Date", "Suspicious_Keyword", "Is_International", "Fraudulent"]
    feature_cols = [c for c in df_engineered.columns if c not in drop_cols]
    X_features = df_engineered[feature_cols].copy()

    # Step 3: Preprocessing Transformation
    try:
        X_transformed = preprocessor.transform(X_features)
    except Exception as e:
        logger.error(f"Error during feature transformation in prediction engine: {e}")
        raise ValueError(f"Feature preprocessing error: {e}")

    # Step 4: Probability Inference
    probabilities = model.predict_proba(X_transformed)[:, 1]
    raw_prob = float(probabilities[0])

    # Step 5: Decision Threshold & Risk Scoring
    selected_threshold = metadata.get("selected_threshold", 0.65) if metadata else 0.65
    risk_thresholds = metadata.get("risk_thresholds", {}) if metadata else {}
    high_th = risk_thresholds.get("high_risk", 0.65)
    med_th = risk_thresholds.get("medium_risk", 0.35)

    risk_info = calculate_risk_score(
        probability=raw_prob,
        high_risk_threshold=high_th,
        medium_risk_threshold=med_th
    )

    result = {
        "transaction_id": str(df_input.get("Transaction_ID", pd.Series(["UNKNOWN"])).iloc[0]),
        "fraud_probability": risk_info["fraud_probability"],
        "fraud_percentage": risk_info["fraud_percentage"],
        "fraud_prediction": int(raw_prob >= selected_threshold),
        "risk_score": risk_info["risk_score"],
        "risk_level": risk_info["risk_level"],
        "action": risk_info["action"],
        "operating_threshold": selected_threshold,
        "model_name": metadata.get("model_name", "LogisticRegression") if metadata else "LogisticRegression"
    }

    return result
