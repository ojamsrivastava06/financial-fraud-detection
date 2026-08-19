"""
Unit tests for feature engineering, categorical encoding, and scikit-learn preprocessing pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from src.features.engineering import build_features
from src.features.encoding import CategoricalEncoder, encode_categorical_features
from src.features.feature_pipeline import create_preprocessing_pipeline, run_feature_pipeline
from src.data.ingestion import load_raw_dataset


def test_build_features_with_real_dataset():
    """Test domain feature creation on raw dataset."""
    df_raw = load_raw_dataset()
    df_feat, created_cols = build_features(df_raw)

    assert isinstance(df_feat, pd.DataFrame)
    assert len(created_cols) == 9
    assert "spend_to_avg_ratio" in df_feat.columns
    assert "is_high_value_transaction" in df_feat.columns
    assert "transaction_hour" in df_feat.columns
    assert "transaction_day_of_week" in df_feat.columns
    assert "is_night_transaction" in df_feat.columns
    assert "is_weekend" in df_feat.columns
    assert "account_age_years" in df_feat.columns
    assert "suspicious_keyword_flag" in df_feat.columns
    assert "is_international_flag" in df_feat.columns


def test_spend_to_avg_ratio_calculation():
    """Verify spend to average ratio mathematical formula."""
    df_dummy = pd.DataFrame({
        "Transaction_Amount": [200.0, 100.0],
        "Average_Spend": [100.0, 200.0]
    })
    df_res, _ = build_features(df_dummy)
    assert round(df_res["spend_to_avg_ratio"].iloc[0], 2) == 2.0
    assert round(df_res["spend_to_avg_ratio"].iloc[1], 2) == 0.5


def test_categorical_encoder():
    """Verify CategoricalEncoder class fits and transforms correctly without data leakage."""
    df_dummy = pd.DataFrame({
        "Merchant_Category": ["Travel", "Health", "Travel"],
        "Payment_Method": ["PayPal", "Credit Card", "PayPal"]
    })
    encoder = CategoricalEncoder(categorical_cols=["Merchant_Category", "Payment_Method"])
    df_encoded = encoder.fit_transform(df_dummy)

    assert isinstance(df_encoded, pd.DataFrame)
    assert encoder.is_fitted is True
    assert "Merchant_Category_Travel" in df_encoded.columns


def test_create_preprocessing_pipeline():
    """Verify scikit-learn ColumnTransformer pipeline creation and transformation."""
    df_raw = load_raw_dataset()
    df_engineered, _ = build_features(df_raw)
    pipeline = create_preprocessing_pipeline()

    X_transformed = pipeline.fit_transform(df_engineered)
    assert isinstance(X_transformed, np.ndarray)
    assert X_transformed.shape[0] == 5000
    assert X_transformed.shape[1] > 10


def test_run_feature_pipeline():
    """Verify end-to-end feature pipeline execution."""
    df_raw = load_raw_dataset()
    X_features, feature_cols = run_feature_pipeline(df_raw)

    assert isinstance(X_features, pd.DataFrame)
    assert len(X_features) == 5000
    assert "Transaction_ID" not in X_features.columns
    assert "Fraudulent" not in X_features.columns
