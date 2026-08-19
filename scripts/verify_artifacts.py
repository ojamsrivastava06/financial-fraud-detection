"""
Model artifact verification script.
Ensures fraud_model.joblib, preprocessor.joblib, and model_metadata.json are loadable and inspectable.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.models.model_registry import ModelRegistry

def verify_artifacts():
    print("=" * 70)
    print("ML ARTIFACT INTEGRITY AUDIT")
    print("=" * 70)

    registry = ModelRegistry()
    model, preprocessor, metadata = registry.load_active_model()

    print(f"1. Model Loaded: {type(model).__name__}")
    print(f"   Model Classes: {getattr(model, 'classes_', None)}")
    print(f"2. Preprocessor Loaded: {type(preprocessor).__name__}")
    print(f"   Transformers in Pipeline: {[t[0] for t in preprocessor.transformers]}")
    print(f"3. Model Metadata:")
    for k, v in metadata.items():
        print(f"   - {k}: {v}")

    assert model is not None, "Trained model object is None"
    assert preprocessor is not None, "Preprocessor object is None"
    assert metadata is not None, "Metadata object is None"
    assert metadata.get("model_name") == "Logistic Regression"
    assert metadata.get("selected_threshold") == 0.65

    print("\n" + "=" * 70)
    print("ML ARTIFACT AUDIT: PASSED (All artifacts valid and loadable)")
    print("=" * 70)

if __name__ == "__main__":
    verify_artifacts()
