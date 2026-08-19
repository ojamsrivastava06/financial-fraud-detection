"""
Domain-specific feature engineering module.
Constructs predictive financial fraud features based strictly on actual dataset columns.
"""

from typing import List, Tuple
import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Constructs domain features from raw dataset columns.

    Features Created:
    - spend_to_avg_ratio: Ratio of transaction amount to customer historical average spend.
    - is_high_value_transaction: Binary flag for transactions exceeding the 95th percentile threshold ($250+).
    - transaction_hour: Hour of transaction (0 - 23) extracted from Transaction_Date.
    - transaction_day_of_week: Day of week (0 = Monday, 6 = Sunday) extracted from Transaction_Date.
    - is_night_transaction: Binary indicator (1 if transaction occurred between 00:00 and 05:59).
    - is_weekend: Binary indicator (1 if transaction occurred on Saturday or Sunday).
    - account_age_years: Customer account age expressed in years.
    - suspicious_keyword_flag: Binary flag (1 if Suspicious_Keyword == 'Yes').
    - is_international_flag: Binary flag (1 if Is_International == 1).

    Returns:
        Tuple of (DataFrame with new features, List of created feature names).
    """
    logger.info("Building domain features from dataset...")
    df_feat = df.copy()
    created_features: List[str] = []

    # 1. Spend-to-Average Ratio
    if "Transaction_Amount" in df_feat.columns and "Average_Spend" in df_feat.columns:
        df_feat["spend_to_avg_ratio"] = (
            df_feat["Transaction_Amount"] / (df_feat["Average_Spend"] + 1e-5)
        ).round(4)
        created_features.append("spend_to_avg_ratio")

    # 2. High-value Transaction Flag (> $250 or > 95th percentile)
    if "Transaction_Amount" in df_feat.columns:
        threshold = df_feat["Transaction_Amount"].quantile(0.95)
        df_feat["is_high_value_transaction"] = (
            df_feat["Transaction_Amount"] > threshold
        ).astype(int)
        created_features.append("is_high_value_transaction")

    # 3. Datetime Features
    if "Transaction_Date" in df_feat.columns:
        dt_series = pd.to_datetime(df_feat["Transaction_Date"], format="%d-%m-%Y %H:%M", errors="coerce")
        if dt_series.notnull().any():
            df_feat["transaction_hour"] = dt_series.dt.hour.fillna(-1).astype(int)
            df_feat["transaction_day_of_week"] = dt_series.dt.dayofweek.fillna(-1).astype(int)
            df_feat["is_night_transaction"] = (
                (df_feat["transaction_hour"] >= 0) & (df_feat["transaction_hour"] <= 5)
            ).astype(int)
            df_feat["is_weekend"] = (df_feat["transaction_day_of_week"] >= 5).astype(int)

            created_features.extend([
                "transaction_hour",
                "transaction_day_of_week",
                "is_night_transaction",
                "is_weekend"
            ])

    # 4. Account Age in Years
    if "Account_Age_Days" in df_feat.columns:
        df_feat["account_age_years"] = (df_feat["Account_Age_Days"] / 365.25).round(2)
        created_features.append("account_age_years")

    # 5. Suspicious Keyword Flag
    if "Suspicious_Keyword" in df_feat.columns:
        df_feat["suspicious_keyword_flag"] = (
            df_feat["Suspicious_Keyword"].astype(str).str.upper() == "YES"
        ).astype(int)
        created_features.append("suspicious_keyword_flag")

    # 6. International Flag
    if "Is_International" in df_feat.columns:
        df_feat["is_international_flag"] = df_feat["Is_International"].astype(int)
        created_features.append("is_international_flag")

    logger.info(f"Engineered {len(created_features)} features: {created_features}")
    return df_feat, created_features
