"""
Production Smoke & Validation Test Suite.
Validates model artifacts, database connectivity, inference pipeline, risk scoring,
and clean Streamlit page execution without eager training dependencies.
"""

import sys
from pathlib import Path
import pytest

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.database.connection import SessionLocal
from src.database.models import TransactionModel, PredictionModel, AlertModel
from src.models.model_registry import ModelRegistry
from src.models.risk_scoring import calculate_risk_score


def test_model_and_preprocessor_artifacts_loading():
    """Verify that ML model binary, fitted preprocessor, and metadata load cleanly."""
    registry = ModelRegistry()
    model, preprocessor, metadata = registry.load_active_model()

    assert model is not None, "Trained model binary failed to load!"
    assert preprocessor is not None, "Preprocessor pipeline failed to load!"
    assert metadata is not None, "Model metadata failed to load!"

    assert metadata.get("model_name") == "Logistic Regression"
    assert metadata.get("selected_threshold") == 0.65
    assert metadata.get("transformed_feature_count") == 34
    assert hasattr(model, "predict_proba"), "Model must provide predict_proba()"


def test_database_connection_and_counts():
    """Verify SQLite database connectivity and expected record counts."""
    db = SessionLocal()
    try:
        tx_count = db.query(TransactionModel).count()
        pred_count = db.query(PredictionModel).count()
        alert_count = db.query(AlertModel).count()

        assert tx_count == 5000, f"Expected 5000 transactions, found {tx_count}"
        assert pred_count == 5000, f"Expected 5000 predictions, found {pred_count}"
        assert alert_count == 1722, f"Expected 1722 alerts, found {alert_count}"
    finally:
        db.close()


def test_risk_scoring_calibration():
    """Verify three-tier risk scoring behavior and threshold boundary logic."""
    # Test low risk
    res_low = calculate_risk_score(0.20)
    assert res_low["risk_level"] == "LOW"
    assert res_low["action"] == "APPROVE"
    assert 0.0 <= res_low["risk_score"] < 35.0

    # Test medium risk
    res_med = calculate_risk_score(0.50)
    assert res_med["risk_level"] == "MEDIUM"
    assert res_med["action"] == "MONITOR"
    assert 35.0 <= res_med["risk_score"] < 65.0

    # Test high risk
    res_high = calculate_risk_score(0.85)
    assert res_high["risk_level"] == "HIGH"
    assert res_high["action"] == "FLAG_FOR_REVIEW"
    assert res_high["risk_score"] >= 65.0


def test_clean_streamlit_import_chain_no_eager_training():
    """Verify dashboard components do not eagerly import training/XGBoost at startup."""
    import dashboard.components.sidebar
    import src.models.model_registry

    # Verify that src.models.train was NOT imported into sys.modules
    assert "src.models.train" not in sys.modules, "src.models.train was eagerly imported!"


def test_dashboard_all_six_pages_execute():
    """Verify that all 6 dashboard page rendering functions execute without unhandled exceptions."""
    from dashboard.pages.overview import render_overview_page
    from dashboard.pages.transactions import render_transactions_page
    from dashboard.pages.fraud_analysis import render_fraud_analysis_page
    from dashboard.pages.risk_analysis import render_risk_analysis_page
    from dashboard.pages.alerts import render_alerts_page
    from dashboard.pages.model_performance import render_model_performance_page

    render_overview_page()
    render_transactions_page()
    render_fraud_analysis_page()
    render_risk_analysis_page()
    render_alerts_page()
    render_model_performance_page()

