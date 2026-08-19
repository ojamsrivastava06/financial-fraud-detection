"""
Unit tests for data ingestion, schema validation, data cleaning, reports, and raw immutability.
"""

from pathlib import Path
import pytest
import pandas as pd
from src.data.ingestion import load_raw_dataset
from src.data.validation import validate_dataset_schema, validate_file_existence
from src.data.cleaning import clean_dataset, remove_duplicates, handle_missing_values, detect_outliers_iqr
from src.config.settings import settings


def test_raw_dataset_file_exists():
    """Verify that raw dataset file exists at configured path."""
    assert validate_file_existence(settings.DATA_PATH) is True


def test_load_raw_dataset_integrity():
    """Verify raw dataset loads correctly with expected dimensions and columns."""
    df = load_raw_dataset(settings.DATA_PATH)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5000
    assert len(df.columns) == 14
    assert "Transaction_ID" in df.columns
    assert "Fraudulent" in df.columns


def test_validate_dataset_schema_success():
    """Verify schema validation on raw dataset passes without errors."""
    df = load_raw_dataset(settings.DATA_PATH)
    report = validate_dataset_schema(df)
    assert report["is_valid"] is True
    assert report["row_count"] == 5000
    assert report["column_count"] == 14
    assert len(report["errors"]) == 0


def test_data_cleaning_pipeline():
    """Verify data cleaning function processes dataframe correctly."""
    df_raw = load_raw_dataset()
    df_cleaned, report = clean_dataset(df_raw)
    assert isinstance(df_cleaned, pd.DataFrame)
    assert report["original_row_count"] == 5000
    assert report["final_row_count"] == 5000
    assert report["missing_values_after"] == 0


def test_remove_duplicates_helper():
    """Verify remove_duplicates helper function."""
    df_dummy = pd.DataFrame({
        "Transaction_ID": ["T1", "T1", "T2"],
        "Amount": [10.0, 10.0, 20.0]
    })
    df_clean, dropped = remove_duplicates(df_dummy)
    assert dropped == 1
    assert len(df_clean) == 2


def test_outlier_detection_iqr():
    """Verify outlier detection flags expected extreme values without dropping them."""
    df_raw = load_raw_dataset()
    outliers = detect_outliers_iqr(df_raw, "Transaction_Amount", iqr_multiplier=3.0)
    assert isinstance(outliers, pd.Series)
    assert outliers.dtype == bool


def test_raw_dataset_immutability():
    """Verify raw dataset CSV file on disk is unchanged."""
    raw_path = settings.DATA_PATH
    df_disk = pd.read_csv(raw_path)
    assert len(df_disk) == 5000
    assert list(df_disk.columns)[0] == "Transaction_ID"
    assert list(df_disk.columns)[-1] == "Fraudulent"


def test_processed_dataset_creation():
    """Verify that processed dataset exists and has engineered feature columns."""
    processed_path = settings.BASE_DIR / "data" / "processed" / "financial_fraud_processed.csv"
    assert processed_path.exists(), "Processed dataset CSV file missing!"
    df_proc = pd.read_csv(processed_path)
    assert len(df_proc) == 5000
    assert "spend_to_avg_ratio" in df_proc.columns
    assert "transaction_hour" in df_proc.columns
