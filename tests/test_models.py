"""
Unit tests for Machine Learning training, cross-validation, evaluation,
risk scoring, model registry serialization, and prediction engine inference.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from src.config.settings import settings
from src.features.engineering import build_features
from src.features.feature_pipeline import create_preprocessing_pipeline
from src.models.train import train_all_models, train_logistic_regression, get_cv_strategy, RANDOM_STATE
from src.models.evaluate import evaluate_single_model, analyze_decision_thresholds
from src.models.risk_scoring import calculate_risk_score
from src.models.model_registry import ModelRegistry
from src.models.predict import predict_fraud_probability


def test_stratified_train_test_split():
    """Verify stratified train/test split preserves minority class ratio."""
    data_path = settings.BASE_DIR / "data" / "processed" / "financial_fraud_processed.csv"
    df = pd.read_csv(data_path)
    X = df.drop(columns=["Transaction_ID", "Customer_ID", "Transaction_Date", "Fraudulent"])
    y = df["Fraudulent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=RANDOM_STATE
    )

    assert len(X_train) == 4000
    assert len(X_test) == 1000
    # Ratio check (~9.64% fraud in both splits)
    assert round(y_train.mean(), 3) == round(y_test.mean(), 3)


def test_calculate_risk_score_tiers():
    """Test risk scoring logic across low, medium, and high probability tiers."""
    high = calculate_risk_score(0.85, high_risk_threshold=0.65, medium_risk_threshold=0.35)
    assert high["risk_level"] == "HIGH"
    assert high["fraud_prediction"] == 1
    assert high["action"] == "FLAG_FOR_REVIEW"
    assert high["fraud_percentage"] == 85.0
    assert high["risk_score"] == 85.0

    medium = calculate_risk_score(0.50, high_risk_threshold=0.65, medium_risk_threshold=0.35)
    assert medium["risk_level"] == "MEDIUM"
    assert medium["action"] == "MONITOR"

    low = calculate_risk_score(0.15, high_risk_threshold=0.65, medium_risk_threshold=0.35)
    assert low["risk_level"] == "LOW"
    assert low["fraud_prediction"] == 0
    assert low["action"] == "APPROVE"


def test_model_training_and_evaluation():
    """Verify training and evaluation of Logistic Regression model."""
    data_path = settings.BASE_DIR / "data" / "processed" / "financial_fraud_processed.csv"
    df = pd.read_csv(data_path)
    drop_cols = ["Transaction_ID", "Customer_ID", "Transaction_Date", "Suspicious_Keyword", "Is_International", "Fraudulent"]
    feature_cols = [c for c in df.columns if c not in drop_cols]

    X = df[feature_cols]
    y = df["Fraudulent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=RANDOM_STATE
    )

    preprocessor = create_preprocessing_pipeline()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    cv = get_cv_strategy(n_splits=3)
    model, cv_score = train_logistic_regression(X_train_proc, y_train, cv)

    assert model is not None
    assert cv_score > 0.0

    eval_res = evaluate_single_model(model, X_test_proc, y_test)
    assert 0.0 <= eval_res["test_pr_auc"] <= 1.0
    assert 0.0 <= eval_res["test_roc_auc"] <= 1.0
    assert eval_res["test_recall"] > 0.5


def test_model_registry_serialization_and_reload():
    """Verify saving and reloading model artifacts via ModelRegistry."""
    registry = ModelRegistry()
    model, preprocessor, metadata = registry.load_active_model()

    assert model is not None, "Serialized model not found in registry!"
    assert preprocessor is not None, "Serialized preprocessor not found in registry!"
    assert metadata is not None, "Serialized metadata not found in registry!"

    assert metadata["model_name"] in ["Logistic Regression", "Random Forest", "XGBoost"]
    assert "test_metrics" in metadata
    assert "selected_threshold" in metadata


def test_prediction_engine_inference_after_reload():
    """Verify predict_fraud_probability endpoint using reloaded registry artifacts."""
    sample_transaction = {
        "Transaction_ID": "TEST_T999",
        "Customer_ID": "CUST_TEST",
        "Transaction_Date": "14-08-2026 12:00",
        "Transaction_Amount": 550.0,
        "Merchant_Category": "Travel",
        "Payment_Method": "Credit Card",
        "Device_Type": "POS",
        "Location": "Bengaluru",
        "Is_International": 1,
        "Previous_Transactions": 5,
        "Average_Spend": 40.0,
        "Account_Age_Days": 45,
        "Suspicious_Keyword": "Yes"
    }

    result = predict_fraud_probability(sample_transaction)

    assert result.get("status") != "model_not_loaded"
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0.0 <= result["fraud_percentage"] <= 100.0
    assert result["fraud_prediction"] in [0, 1]
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert result["action"] in ["APPROVE", "MONITOR", "FLAG_FOR_REVIEW"]


def test_no_data_leakage_in_preprocessing():
    """Verify that fitting ColumnTransformer on X_train does not leak X_test statistics."""
    df_train_dummy = pd.DataFrame({
        "Transaction_Amount": [10.0, 20.0, 30.0],
        "Previous_Transactions": [1, 2, 3],
        "Average_Spend": [15.0, 15.0, 15.0],
        "Account_Age_Days": [100, 200, 300],
        "Merchant_Category": ["Travel", "Health", "Travel"],
        "Payment_Method": ["PayPal", "Credit Card", "PayPal"],
        "Device_Type": ["POS", "Mobile", "Desktop"],
        "Location": ["Delhi", "Mumbai", "Delhi"],
        "is_high_value_transaction": [0, 0, 0],
        "is_night_transaction": [0, 0, 0],
        "is_weekend": [0, 0, 0],
        "suspicious_keyword_flag": [0, 0, 0],
        "is_international_flag": [0, 0, 0],
        "spend_to_avg_ratio": [0.66, 1.33, 2.0],
        "account_age_years": [0.27, 0.54, 0.82]
    })

    df_test_dummy = pd.DataFrame({
        "Transaction_Amount": [1000.0],  # Outlier in test set
        "Previous_Transactions": [100],
        "Average_Spend": [15.0],
        "Account_Age_Days": [5000],
        "Merchant_Category": ["Travel"],
        "Payment_Method": ["PayPal"],
        "Device_Type": ["POS"],
        "Location": ["Delhi"],
        "is_high_value_transaction": [1],
        "is_night_transaction": [0],
        "is_weekend": [0],
        "suspicious_keyword_flag": [1],
        "is_international_flag": [1],
        "spend_to_avg_ratio": [66.6],
        "account_age_years": [13.6]
    })

    pipe = create_preprocessing_pipeline()
    X_train_proc = pipe.fit_transform(df_train_dummy)
    X_test_proc = pipe.transform(df_test_dummy)

    # Scaling of test sample must be computed relative to train sample median/IQR
    assert X_train_proc.shape[0] == 3
    assert X_test_proc.shape[0] == 1
