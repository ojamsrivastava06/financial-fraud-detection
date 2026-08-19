"""
Model Registry module for safe serialization, versioning, metadata storage,
and loading of trained models and preprocessing pipelines.
"""

from pathlib import Path
import json
import datetime
from typing import Dict, Any, Optional, Tuple
import joblib
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelRegistry:
    """Model Registry class to save, version, and deserialize ML artifacts."""

    _cached_model: Optional[Any] = None
    _cached_preprocessor: Optional[Any] = None
    _cached_metadata: Optional[Dict[str, Any]] = None
    _cached_paths: Tuple[Optional[str], Optional[str], Optional[str]] = (None, None, None)

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.BASE_DIR
        self.trained_dir = self.base_dir / "models" / "trained"
        self.preprocessing_dir = self.base_dir / "models" / "preprocessing"
        self.metadata_dir = self.base_dir / "models" / "metadata"

        # Ensure artifact directories exist
        self.trained_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessing_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_model_artifacts(
        self,
        model: Any,
        preprocessor: Any,
        metadata: Dict[str, Any],
        model_filename: str = "fraud_model.joblib",
        preprocessor_filename: str = "preprocessor.joblib",
        metadata_filename: str = "model_metadata.json"
    ) -> Tuple[Path, Path, Path]:
        """
        Serializes model, preprocessing pipeline, and metadata to disk.
        """
        # Sanitize filenames to prevent path traversal
        model_filename = Path(model_filename).name
        preprocessor_filename = Path(preprocessor_filename).name
        metadata_filename = Path(metadata_filename).name

        model_path = (self.trained_dir / model_filename).resolve()
        preprocessor_path = (self.preprocessing_dir / preprocessor_filename).resolve()
        metadata_path = (self.metadata_dir / metadata_filename).resolve()

        # Add timestamp if not present
        metadata["saved_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        logger.info(f"Saving trained model to {model_path}...")
        joblib.dump(model, model_path)

        logger.info(f"Saving preprocessing pipeline to {preprocessor_path}...")
        joblib.dump(preprocessor, preprocessor_path)

        logger.info(f"Saving model metadata to {metadata_path}...")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Update cache
        ModelRegistry._cached_model = model
        ModelRegistry._cached_preprocessor = preprocessor
        ModelRegistry._cached_metadata = metadata
        ModelRegistry._cached_paths = (str(model_path), str(preprocessor_path), str(metadata_path))

        logger.info("Successfully serialized all model artifacts.")
        return model_path, preprocessor_path, metadata_path

    def load_active_model(
        self,
        model_filename: str = "fraud_model.joblib",
        preprocessor_filename: str = "preprocessor.joblib",
        metadata_filename: str = "model_metadata.json",
        reload: bool = False
    ) -> Tuple[Optional[Any], Optional[Any], Optional[Dict[str, Any]]]:
        """
        Loads active production model, preprocessor, and metadata from disk or in-memory cache.
        """
        # Sanitize filenames to prevent path traversal
        model_filename = Path(model_filename).name
        preprocessor_filename = Path(preprocessor_filename).name
        metadata_filename = Path(metadata_filename).name

        model_path = (self.trained_dir / model_filename).resolve()
        preprocessor_path = (self.preprocessing_dir / preprocessor_filename).resolve()
        metadata_path = (self.metadata_dir / metadata_filename).resolve()

        current_paths = (str(model_path), str(preprocessor_path), str(metadata_path))

        if (
            not reload
            and ModelRegistry._cached_model is not None
            and ModelRegistry._cached_preprocessor is not None
            and ModelRegistry._cached_metadata is not None
            and ModelRegistry._cached_paths == current_paths
        ):
            return ModelRegistry._cached_model, ModelRegistry._cached_preprocessor, ModelRegistry._cached_metadata

        if not (model_path.exists() and preprocessor_path.exists() and metadata_path.exists()):
            logger.warning("Active model artifacts not found in registry.")
            return None, None, None

        logger.info("Loading active model artifacts from registry...")
        model = joblib.load(model_path)
        preprocessor = joblib.load(preprocessor_path)

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Cache in memory
        ModelRegistry._cached_model = model
        ModelRegistry._cached_preprocessor = preprocessor
        ModelRegistry._cached_metadata = metadata
        ModelRegistry._cached_paths = current_paths

        return model, preprocessor, metadata
