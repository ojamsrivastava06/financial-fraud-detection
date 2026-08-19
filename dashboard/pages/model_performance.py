"""
Streamlit Model Performance & Metrics Dashboard Page.
Displays actual Phase 3 test set evaluation metrics, ROC/PR curves, confusion matrix, and feature importances.
"""

from pathlib import Path
import sys

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import streamlit as st
import pandas as pd
from PIL import Image
from src.config.settings import settings


def render_model_performance_page():
    """Renders Machine Learning Model Performance Metrics Page."""
    st.markdown(
        """
        <div class="main-header">
            <h1>🎯 Model Performance & Evaluation Metrics</h1>
            <p>Measured test-set performance metrics, ROC curves, Precision-Recall curves, confusion matrices, and feature importances.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    base_dir = settings.BASE_DIR
    meta_path = base_dir / "models" / "metadata" / "model_metadata.json"
    comp_path = base_dir / "reports" / "model_reports" / "model_comparison.csv"
    fig_dir = base_dir / "reports" / "figures"

    # Display Active Model Metadata Header
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        test_m = meta.get("test_metrics", {})
        st.subheader(f"🏆 Active Model: {meta.get('model_name')} (v{meta.get('model_version')})")

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            st.metric("Test PR-AUC", f"{test_m.get('test_pr_auc', 0.0):.4f}")
        with m2:
            st.metric("Test ROC-AUC", f"{test_m.get('test_roc_auc', 0.0):.4f}")
        with m3:
            st.metric("Test Precision", f"{test_m.get('test_precision', 0.0):.4f}")
        with m4:
            st.metric("Test Recall", f"{test_m.get('test_recall', 0.0):.4f}")
        with m5:
            st.metric("Test F1 Score", f"{test_m.get('test_f1', 0.0):.4f}")
        with m6:
            st.metric("Test Accuracy", f"{test_m.get('test_accuracy', 0.0) * 100:.1f}%")
    else:
        st.info("ℹ️ Model metadata file not found at expected path.")

    st.markdown("---")

    # Candidate Model Comparison Table
    st.subheader("📊 Candidate Model Benchmark Comparison")
    if comp_path.exists():
        df_comp = pd.read_csv(comp_path)
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Model comparison report not found.")

    st.markdown("---")

    # Evaluation Figures Grid
    col_roc, col_pr = st.columns(2)

    with col_roc:
        st.subheader("📈 ROC Curves Comparison")
        roc_img_path = fig_dir / "model_roc_comparison.png"
        if roc_img_path.exists():
            st.image(str(roc_img_path), use_container_width=True)
        else:
            st.info("ROC comparison image not found.")

    with col_pr:
        st.subheader("🎯 Precision-Recall Curves Comparison")
        pr_img_path = fig_dir / "model_pr_comparison.png"
        if pr_img_path.exists():
            st.image(str(pr_img_path), use_container_width=True)
        else:
            st.info("PR comparison image not found.")

    st.markdown("---")

    col_cm, col_fi = st.columns(2)

    with col_cm:
        st.subheader("🧩 Confusion Matrix (Active Model)")
        cm_img_path = fig_dir / "logistic_regression_confusion_matrix.png"
        if not cm_img_path.exists():
            cm_img_path = fig_dir / "xgboost_confusion_matrix.png"

        if cm_img_path.exists():
            st.image(str(cm_img_path), use_container_width=True)
        else:
            st.info("Confusion matrix image not found.")

    with col_fi:
        st.subheader("⭐ Feature Importance / Coefficient Ranking")
        fi_img_path = fig_dir / "feature_importance.png"
        if fi_img_path.exists():
            st.image(str(fi_img_path), use_container_width=True)
        else:
            st.info("Feature importance image not found.")


if __name__ == "__main__":
    render_model_performance_page()
