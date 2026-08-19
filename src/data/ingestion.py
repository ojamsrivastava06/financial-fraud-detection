"""
Data ingestion module for loading dataset without modifying raw files.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_raw_dataset(file_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw transaction CSV dataset into a Pandas DataFrame.
    Does NOT modify the source file.
    """
    target_path = Path(file_path) if file_path else settings.DATA_PATH

    if not target_path.exists():
        logger.error(f"Raw dataset file not found at: {target_path}")
        raise FileNotFoundError(f"Raw dataset not found at {target_path}")

    logger.info(f"Loading raw dataset from {target_path}...")
    df = pd.read_csv(target_path)
    logger.info(f"Loaded dataset with shape {df.shape}")
    return df
