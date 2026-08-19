"""
Report generation script for dataset profiling, target analysis, and data quality metrics.
"""

from pathlib import Path
import sys
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.data.ingestion import load_raw_dataset
from src.data.validation import validate_dataset_schema
from src.data.cleaning import clean_dataset
from src.features.engineering import build_features
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_dataset_profile(df: pd.DataFrame) -> Tuple[dict, pd.DataFrame]:
    """Generates comprehensive dataset profile JSON and summary CSV."""
    total_rows, total_cols = df.shape
    duplicate_rows = int(df.duplicated().sum())

    columns_meta = []
    num_cols, cat_cols, date_cols, bool_cols, id_cols = [], [], [], [], []

    for col in df.columns:
        dtype_str = str(df[col].dtype)
        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / total_rows) * 100, 2)
        unique_count = int(df[col].nunique())
        sample_vals = [str(x) for x in df[col].dropna().unique()[:3]]

        # Role determination
        if col in ["Transaction_ID", "Customer_ID"]:
            role = "identifier"
            id_cols.append(col)
        elif col in ["Fraudulent"]:
            role = "target"
        elif col in ["Transaction_Date"]:
            role = "datetime feature"
            date_cols.append(col)
        elif col in ["Is_International"]:
            role = "boolean feature"
            bool_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            role = "numerical feature"
            num_cols.append(col)
        else:
            role = "categorical feature"
            cat_cols.append(col)

        columns_meta.append({
            "column_name": col,
            "data_type": dtype_str,
            "role": role,
            "unique_values": unique_count,
            "missing_count": null_count,
            "missing_percentage": null_pct,
            "sample_values": sample_vals
        })

    profile = {
        "dataset_name": "financial_fraud_detection_dataset.csv",
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_rows": duplicate_rows,
        "constant_columns": [col for col in df.columns if df[col].nunique() <= 1],
        "numerical_columns": num_cols,
        "categorical_columns": cat_cols,
        "datetime_columns": date_cols,
        "boolean_columns": bool_cols,
        "identifier_columns": id_cols,
        "target_column": "Fraudulent",
        "columns_detail": columns_meta
    }

    summary_df = pd.DataFrame(columns_meta)
    return profile, summary_df


def generate_target_distribution_report(df: pd.DataFrame) -> dict:
    """Generates target distribution stats and exports visualization figure."""
    target_col = "Fraudulent"
    counts = df[target_col].value_counts().to_dict()
    total = len(df)

    genuine_count = int(counts.get(0, 0))
    fraud_count = int(counts.get(1, 0))
    genuine_pct = round((genuine_count / total) * 100, 2)
    fraud_pct = round((fraud_count / total) * 100, 2)
    imbalance_ratio = round(genuine_count / max(fraud_count, 1), 2)

    target_report = {
        "target_column": target_col,
        "total_samples": total,
        "genuine_count": genuine_count,
        "genuine_percentage": genuine_pct,
        "fraud_count": fraud_count,
        "fraud_percentage": fraud_pct,
        "imbalance_ratio": f"{imbalance_ratio}:1",
        "target_values": {
            "0": "Genuine Transaction",
            "1": "Fraudulent Transaction"
        }
    }

    # Generate Target Distribution Visualization PNG
    plt.figure(figsize=(8, 5))
    sns.set_theme(style="whitegrid")
    ax = sns.barplot(
        x=["Genuine (0)", "Fraudulent (1)"],
        y=[genuine_count, fraud_count],
        hue=["Genuine (0)", "Fraudulent (1)"],
        palette=["#38bdf8", "#ef4444"],
        legend=False
    )
    plt.title("Financial Fraud Target Class Distribution", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Class", fontsize=12)
    plt.ylabel("Transaction Count", fontsize=12)

    for p in ax.patches:
        height = p.get_height()
        pct = (height / total) * 100
        ax.annotate(
            f"{int(height):,} ({pct:.1f}%)",
            (p.get_x() + p.get_width() / 2., height / 2),
            ha="center", va="center", fontsize=11, color="white", fontweight="bold"
        )

    plt.tight_layout()
    fig_path = Path("reports/figures/target_distribution.png")
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=300)
    plt.close()
    logger.info(f"Target distribution chart saved to {fig_path}")

    return target_report


def run_profiling_and_reports():
    """Main execution function to generate dataset profiling artifacts."""
    logger.info("Executing dataset profiling and report generation...")
    df_raw = load_raw_dataset()

    # 1. Dataset Profile & Summary CSV
    profile, summary_df = generate_dataset_profile(df_raw)

    profile_path = Path("reports/data_quality/dataset_profile.json")
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    logger.info(f"Dataset profile JSON saved to {profile_path}")

    summary_csv_path = Path("reports/data_quality/dataset_summary.csv")
    summary_df.to_csv(summary_csv_path, index=False)
    logger.info(f"Dataset summary CSV saved to {summary_csv_path}")

    # 2. Target Distribution Report & Chart
    target_report = generate_target_distribution_report(df_raw)
    target_path = Path("reports/data_quality/target_distribution.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(target_report, f, indent=2)
    logger.info(f"Target distribution report JSON saved to {target_path}")

    # 3. Clean Dataset & Generate Cleaning Report
    df_cleaned, cleaning_report = clean_dataset(df_raw)
    df_engineered, created_features = build_features(df_cleaned)
    cleaning_report["features_created"] = created_features
    cleaning_report["warnings"] = validate_dataset_schema(df_raw)["warnings"]

    cleaning_path = Path("reports/data_quality/cleaning_report.json")
    with open(cleaning_path, "w", encoding="utf-8") as f:
        json.dump(cleaning_report, f, indent=2)
    logger.info(f"Cleaning report JSON saved to {cleaning_path}")


if __name__ == "__main__":
    run_profiling_and_reports()
