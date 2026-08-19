"""
End-to-end Phase 2 Data Pipeline Execution Script.
Executes ingestion, validation, cleaning, feature engineering, processed dataset export,
and data quality report generation.
"""

from pathlib import Path
import sys

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.data.ingestion import load_raw_dataset
from src.data.validation import validate_dataset_schema
from src.data.cleaning import clean_dataset
from src.features.engineering import build_features
from src.features.encoding import encode_categorical_features
from scripts.generate_reports import run_profiling_and_reports
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_full_pipeline():
    """Executes the full Phase 2 data processing workflow."""
    logger.info("==================================================")
    logger.info("STARTING PHASE 2 DATA PROCESSING PIPELINE")
    logger.info("==================================================")

    # 1. Load Raw Dataset
    df_raw = load_raw_dataset()
    logger.info(f"Loaded raw dataset shape: {df_raw.shape}")

    # 2. Validate Schema & Integrity
    val_report = validate_dataset_schema(df_raw)
    if not val_report["is_valid"]:
        logger.error(f"Dataset validation failed: {val_report['errors']}")
        sys.exit(1)

    # 3. Clean Dataset
    df_cleaned, clean_report = clean_dataset(df_raw)

    # 4. Feature Engineering
    df_engineered, created_features = build_features(df_cleaned)
    logger.info(f"Engineered {len(created_features)} features: {created_features}")

    # 5. Export Processed Data (data/processed/financial_fraud_processed.csv)
    output_path = settings.BASE_DIR / "data" / "processed" / "financial_fraud_processed.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_engineered.to_csv(output_path, index=False)
    logger.info(f"Successfully saved processed dataset to: {output_path}")

    # 6. Generate Data Quality Reports & Figures
    run_profiling_and_reports()

    logger.info("==================================================")
    logger.info("PHASE 2 DATA PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("==================================================")


if __name__ == "__main__":
    run_full_pipeline()
