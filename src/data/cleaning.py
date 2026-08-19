"""
Data cleaning module for handling duplicates, missing values, string normalization,
datetime parsing, and configurable outlier detection.
"""

from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)


def remove_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> Tuple[pd.DataFrame, int]:
    """
    Remove duplicate rows from DataFrame.
    Returns cleaned DataFrame copy and count of dropped duplicates.
    """
    initial_count = len(df)
    df_cleaned = df.drop_duplicates(subset=subset).copy()
    dropped_count = initial_count - len(df_cleaned)
    if dropped_count > 0:
        logger.info(f"Removed {dropped_count} duplicate rows.")
    return df_cleaned, dropped_count


def normalize_strings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean whitespace and standardize capitalization for all string/object columns.
    """
    df_cleaned = df.copy()
    for col in df_cleaned.select_dtypes(include=["object"]).columns:
        df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
    return df_cleaned


def parse_datetime_columns(
    df: pd.DataFrame,
    date_columns: Optional[List[str]] = None,
    date_format: str = "%d-%m-%Y %H:%M"
) -> pd.DataFrame:
    """
    Parse date/time string columns into pandas Datetime Series.
    """
    df_cleaned = df.copy()
    cols = date_columns or ["Transaction_Date"]

    for col in cols:
        if col in df_cleaned.columns:
            logger.info(f"Parsing datetime column '{col}' with format '{date_format}'...")
            df_cleaned[col] = pd.to_datetime(df_cleaned[col], format=date_format, errors="coerce")
    return df_cleaned


def handle_missing_values(
    df: pd.DataFrame,
    strategy_numeric: str = "median",
    strategy_categorical: str = "mode"
) -> pd.DataFrame:
    """
    Impute missing values for numerical and categorical columns according to specified strategies.
    Does not drop rows unless specified.
    """
    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        null_count = df_cleaned[col].isnull().sum()
        if null_count > 0:
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                val = df_cleaned[col].median() if strategy_numeric == "median" else df_cleaned[col].mean()
                df_cleaned[col] = df_cleaned[col].fillna(val)
                logger.info(f"Imputed {null_count} missing numeric values in '{col}' with {strategy_numeric} ({val}).")
            else:
                val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else "Unknown"
                df_cleaned[col] = df_cleaned[col].fillna(val)
                logger.info(f"Imputed {null_count} missing categorical values in '{col}' with mode ({val}).")

    return df_cleaned


def detect_outliers_iqr(
    df: pd.DataFrame,
    column: str,
    iqr_multiplier: float = 3.0
) -> pd.Series:
    """
    Configurable IQR outlier detection for numerical feature.
    NOTE: High-value transactions are common in financial fraud datasets.
    This function flags potential outliers for analysis rather than silently dropping them.

    Returns:
        Boolean Series where True indicates an outlier based on IQR multiplier.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - (iqr_multiplier * IQR)
    upper_bound = Q3 + (iqr_multiplier * IQR)

    is_outlier = (df[column] < lower_bound) | (df[column] > upper_bound)
    outlier_count = is_outlier.sum()
    logger.info(f"IQR Outlier detection on '{column}' (k={iqr_multiplier}): {outlier_count} outliers flagged.")
    return is_outlier


def clean_dataset(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes full data cleaning pipeline on DataFrame copy.

    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict).
    """
    logger.info("Executing full data cleaning pipeline...")
    initial_rows = len(df)
    initial_nulls = int(df.isnull().sum().sum())

    # 1. Normalize strings
    df_cleaned = normalize_strings(df)

    # 2. Parse datetimes
    df_cleaned = parse_datetime_columns(df_cleaned)

    # 3. Remove duplicates
    df_cleaned, dropped_duplicates = remove_duplicates(df_cleaned)

    # 4. Handle missing values
    df_cleaned = handle_missing_values(df_cleaned)

    final_nulls = int(df_cleaned.isnull().sum().sum())
    final_rows = len(df_cleaned)

    # 5. Outlier summary flag for transaction amount
    outliers_flagged = int(detect_outliers_iqr(df_cleaned, "Transaction_Amount", iqr_multiplier=3.0).sum())

    cleaning_report = {
        "original_row_count": initial_rows,
        "final_row_count": final_rows,
        "rows_removed": initial_rows - final_rows,
        "duplicate_count": dropped_duplicates,
        "missing_values_before": initial_nulls,
        "missing_values_after": final_nulls,
        "outliers_flagged_transaction_amount": outliers_flagged,
        "columns_transformed": list(df_cleaned.columns),
    }

    logger.info(f"Data cleaning complete: {initial_rows} -> {final_rows} rows.")
    return df_cleaned, cleaning_report
