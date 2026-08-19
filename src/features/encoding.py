"""
Categorical encoding module.
Provides One-Hot Encoding for low-cardinality categorical features
and prevents data leakage by supporting separate fit/transform methods.
"""

from typing import List, Tuple, Optional
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Nominal categorical columns in actual dataset
NOMINAL_CATEGORICAL_COLUMNS = [
    "Merchant_Category",
    "Payment_Method",
    "Device_Type",
    "Location",
]


class CategoricalEncoder:
    """
    Wrapper for OneHotEncoder targeting categorical features in fraud detection data.
    Fits strictly on training split to prevent data leakage.
    """

    def __init__(self, categorical_cols: Optional[List[str]] = None):
        self.categorical_cols = categorical_cols or NOMINAL_CATEGORICAL_COLUMNS
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        self.is_fitted = False
        self.feature_names: List[str] = []

    def fit(self, df: pd.DataFrame) -> "CategoricalEncoder":
        """Fit OneHotEncoder on categorical columns of training DataFrame."""
        existing_cols = [c for c in self.categorical_cols if c in df.columns]
        if existing_cols:
            self.encoder.fit(df[existing_cols])
            self.feature_names = list(self.encoder.get_feature_names_out(existing_cols))
            self.is_fitted = True
            logger.info(f"Fitted CategoricalEncoder on columns {existing_cols}. Generated {len(self.feature_names)} features.")
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform categorical columns into One-Hot Encoded DataFrame."""
        if not self.is_fitted:
            raise ValueError("CategoricalEncoder must be fitted before calling transform().")

        df_res = df.copy()
        existing_cols = [c for c in self.categorical_cols if c in df_res.columns]

        if existing_cols:
            encoded_array = self.encoder.transform(df_res[existing_cols])
            encoded_df = pd.DataFrame(
                encoded_array,
                columns=self.feature_names,
                index=df_res.index
            )
            df_res = df_res.drop(columns=existing_cols)
            df_res = pd.concat([df_res, encoded_df], axis=1)

        return df_res

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit encoder and transform DataFrame in one step."""
        return self.fit(df).transform(df)


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function for quick full-dataset encoding (e.g. for exploratory feature matrix creation).
    Note: For model training pipelines, use CategoricalEncoder class inside train/test split.
    """
    encoder = CategoricalEncoder()
    return encoder.fit_transform(df)
