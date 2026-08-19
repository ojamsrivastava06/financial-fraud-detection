"""
Scikit-learn compatible preprocessing pipeline builder.
Encapsulates numerical scaling, categorical one-hot encoding, and missing value imputation
into a reusable ColumnTransformer / Pipeline.
"""

from typing import List, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from src.features.engineering import build_features
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default column groupings based on actual dataset inspection
DEFAULT_NUMERICAL_COLS = [
    "Transaction_Amount",
    "Previous_Transactions",
    "Average_Spend",
    "Account_Age_Days",
    "spend_to_avg_ratio",
    "account_age_years",
]

DEFAULT_CATEGORICAL_COLS = [
    "Merchant_Category",
    "Payment_Method",
    "Device_Type",
    "Location",
]

DEFAULT_BINARY_COLS = [
    "is_high_value_transaction",
    "is_night_transaction",
    "is_weekend",
    "suspicious_keyword_flag",
    "is_international_flag",
]


def create_preprocessing_pipeline(
    numerical_cols: Optional[List[str]] = None,
    categorical_cols: Optional[List[str]] = None,
    binary_cols: Optional[List[str]] = None,
    use_robust_scaler: bool = True
) -> ColumnTransformer:
    """
    Creates a scikit-learn ColumnTransformer pipeline for preprocessing features.

    Numerical Pipeline: SimpleImputer(median) -> RobustScaler / StandardScaler
    Categorical Pipeline: SimpleImputer(most_frequent) -> OneHotEncoder(handle_unknown='ignore')
    Binary Pipeline: SimpleImputer(most_frequent) -> Passthrough

    Returns:
        Configured ColumnTransformer instance.
    """
    num_cols = numerical_cols or DEFAULT_NUMERICAL_COLS
    cat_cols = categorical_cols or DEFAULT_CATEGORICAL_COLS
    bin_cols = binary_cols or DEFAULT_BINARY_COLS

    scaler = RobustScaler() if use_robust_scaler else StandardScaler()

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", scaler)
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(sparse_output=False, handle_unknown="ignore"))
    ])

    bin_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, num_cols),
            ("cat", cat_pipeline, cat_cols),
            ("bin", bin_pipeline, bin_cols)
        ],
        remainder="drop"
    )

    logger.info("Created scikit-learn preprocessing ColumnTransformer pipeline.")
    return preprocessor


def run_feature_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    End-to-end feature transformation pipeline execution for data preparation.

    1. Executes feature engineering (`build_features`).
    2. Drops raw non-feature identifier and timestamp string columns.

    Returns:
        Tuple of (Feature DataFrame ready for modeling, List of feature column names).
    """
    logger.info("Executing end-to-end feature pipeline...")

    # Step 1: Build domain features
    df_engineered, created_features = build_features(df)

    # Step 2: Select feature set (exclude ID and raw timestamp columns)
    drop_cols = ["Transaction_ID", "Customer_ID", "Transaction_Date", "Suspicious_Keyword", "Is_International", "Fraudulent"]
    feature_cols = [c for c in df_engineered.columns if c not in drop_cols]

    X_features = df_engineered[feature_cols].copy()
    logger.info(f"Feature pipeline returned {len(feature_cols)} features for modeling.")
    return X_features, feature_cols
