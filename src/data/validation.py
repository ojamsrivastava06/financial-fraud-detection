"""
Data quality validation module for checking raw and processed dataset integrity.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Primary raw columns expected in dataset
EXPECTED_RAW_COLUMNS = [
    "Transaction_ID",
    "Customer_ID",
    "Transaction_Date",
    "Transaction_Amount",
    "Merchant_Category",
    "Payment_Method",
    "Device_Type",
    "Location",
    "Is_International",
    "Previous_Transactions",
    "Average_Spend",
    "Account_Age_Days",
    "Suspicious_Keyword",
    "Fraudulent",
]

ALLOWED_CATEGORIES = {
    "Merchant_Category": ["Travel", "Utilities", "Entertainment", "Health", "Fashion", "Grocery", "Food", "Electronics"],
    "Payment_Method": ["PayPal", "Debit Card", "NetBanking", "Credit Card", "UPI"],
    "Device_Type": ["POS", "Mobile", "Desktop"],
    "Location": ["Bengaluru", "Kolkata", "Mumbai", "Delhi", "Chennai", "Pune", "Hyderabad"],
    "Suspicious_Keyword": ["No", "Yes", "NO", "YES", "no", "yes"],
}


class DataValidationError(Exception):
    """Custom exception raised when data validation encounters critical failures."""
    pass


def validate_file_existence(file_path: Path) -> bool:
    """Validate that specified file path exists on disk."""
    if not file_path.exists():
        logger.error(f"Validation Error: File does not exist at {file_path}")
        raise FileNotFoundError(f"Dataset file missing at {file_path}")
    return True


def validate_dataset_schema(df: pd.DataFrame, expected_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Comprehensive validation of dataset schema, column presence, null values,
    duplicates, numerical bounds, categorical values, target validity, and key uniqueness.
    """
    logger.info("Executing comprehensive data quality validation...")
    expected_cols = expected_columns or EXPECTED_RAW_COLUMNS
    warnings: List[str] = []
    errors: List[str] = []

    # 1. Non-empty check
    if df.empty:
        errors.append("Dataset is empty (0 rows).")

    # 2. Required columns check
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # 3. Duplicate records check
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        warnings.append(f"Found {duplicate_count} duplicate rows in dataset.")

    # 4. Identifier uniqueness check
    if "Transaction_ID" in df.columns:
        unique_tx_ids = df["Transaction_ID"].nunique()
        total_tx_ids = len(df["Transaction_ID"])
        if unique_tx_ids < total_tx_ids:
            warnings.append(f"Transaction_ID has {total_tx_ids - unique_tx_ids} duplicate entries.")

    # 5. Missing values check
    null_summary = df.isnull().sum().to_dict()
    total_nulls = sum(null_summary.values())
    if total_nulls > 0:
        warnings.append(f"Found total {total_nulls} missing values across columns.")

    # 6. Impossible numerical values check
    if "Transaction_Amount" in df.columns:
        negative_amounts = (df["Transaction_Amount"] < 0).sum()
        if negative_amounts > 0:
            errors.append(f"Found {negative_amounts} negative Transaction_Amount values.")

    if "Average_Spend" in df.columns:
        negative_spend = (df["Average_Spend"] < 0).sum()
        if negative_spend > 0:
            errors.append(f"Found {negative_spend} negative Average_Spend values.")

    if "Account_Age_Days" in df.columns:
        negative_age = (df["Account_Age_Days"] < 0).sum()
        if negative_age > 0:
            errors.append(f"Found {negative_age} negative Account_Age_Days values.")

    if "Previous_Transactions" in df.columns:
        negative_tx = (df["Previous_Transactions"] < 0).sum()
        if negative_tx > 0:
            errors.append(f"Found {negative_tx} negative Previous_Transactions values.")

    # 7. Invalid categorical values check
    for cat_col, allowed_vals in ALLOWED_CATEGORIES.items():
        if cat_col in df.columns:
            invalid_vals = set(df[cat_col].dropna().unique()) - set(allowed_vals)
            if invalid_vals:
                warnings.append(f"Unexpected categorical values in {cat_col}: {invalid_vals}")

    # 8. Target validity check
    if "Fraudulent" in df.columns:
        invalid_target = set(df["Fraudulent"].dropna().unique()) - {0, 1}
        if invalid_target:
            errors.append(f"Invalid target values in Fraudulent column: {invalid_target}")

    is_valid = len(errors) == 0

    validation_report = {
        "is_valid": is_valid,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_count": duplicate_count,
        "total_null_count": total_nulls,
        "null_details": null_summary,
        "warnings": warnings,
        "errors": errors,
    }

    if is_valid:
        logger.info(f"Data validation passed with {len(warnings)} warning(s).")
    else:
        logger.error(f"Data validation failed with {len(errors)} error(s): {errors}")

    return validation_report
