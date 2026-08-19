"""
Data preprocessing pipeline skeleton.
"""

from typing import Tuple
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


def preprocess_data(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Splits features and target, prepares datasets for pipeline.

    TODO [PHASE 2]: Implement scaling, train/test split, and encoding hooks.
    """
    logger.info("Data preprocessing skeleton called [Awaiting Phase 2 implementation]")
    target_col = "Fraudulent"
    if target_col in df.columns:
        X = df.drop(columns=[target_col])
        y = df[target_col]
    else:
        X = df.copy()
        y = pd.Series(dtype=int)
    return X, y
