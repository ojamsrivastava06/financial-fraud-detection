"""
Streamlit Risk Analysis & Calibration Dashboard Page.
Hydrated with real model probability distributions and decision boundary thresholds.
"""

from pathlib import Path
import sys

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from src.database.connection import SessionLocal
from src.database.repository import TransactionRepository
from src.models.model_registry import ModelRegistry


def render_risk_analysis_page():
    """Renders Risk Probability Distribution & Tier Calibration Page."""
    st.markdown(
        """
        <div class="main-header">
            <h1>⚖️ Fraud Risk Scoring & Tier Analysis</h1>
            <p>Risk probability distribution, score calibration, and operating threshold sensitivity analysis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        db = SessionLocal()
        registry = ModelRegistry()
        _, _, metadata = registry.load_active_model()

        try:
            query_sql = text("SELECT * FROM transactions")
            df = pd.read_sql(query_sql, db.bind)

            if df.empty:
                st.info("No transaction records available for risk analysis.")
                return

            # Clean and fill any missing probability or risk values
            df["fraud_probability"] = df["fraud_probability"].fillna(0.0)
            df["risk_score"] = df["risk_score"].fillna(0.0)
            df["risk_level"] = df["risk_level"].fillna("LOW")
            df["transaction_amount"] = df["transaction_amount"].fillna(0.0)
            df["customer_id"] = df["customer_id"].fillna("Unknown")
            df["merchant_category"] = df["merchant_category"].fillna("Unknown")

            # Display Active Model Risk Configuration Metadata
            if metadata:
                st.markdown("### ⚙️ Operating Risk Threshold Configuration")
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.write(f"**Operating Model:** `{metadata.get('model_name')}`")
                with m2:
                    st.write(f"**Decision Threshold:** `{metadata.get('selected_threshold', 0.65)}`")
                with m3:
                    st.write(f"**Low Risk Range:** `< {metadata.get('risk_thresholds', {}).get('low_risk', 0.35)}`")
                with m4:
                    st.write(f"**High Risk Range:** `≥ {metadata.get('risk_thresholds', {}).get('high_risk', 0.65)}`")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Probability Score Distribution")
                fig_hist = px.histogram(
                    df,
                    x="fraud_probability",
                    color="risk_level",
                    nbins=30,
                    color_discrete_map={"LOW": "#22c55e", "MEDIUM": "#eab308", "HIGH": "#ef4444"},
                    labels={"fraud_probability": "Predicted Fraud Probability", "count": "Frequency"},
                    title="Probability Histogram by Risk Tier"
                )
                fig_hist.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                st.subheader("🎯 Risk Score vs Transaction Amount")
                fig_scatter = px.scatter(
                    df,
                    x="transaction_amount",
                    y="fraud_probability",
                    color="risk_level",
                    hover_data=["transaction_id", "customer_id", "merchant_category"],
                    color_discrete_map={"LOW": "#22c55e", "MEDIUM": "#eab308", "HIGH": "#ef4444"},
                    labels={"transaction_amount": "Transaction Amount ($)", "fraud_probability": "Fraud Probability"},
                    title="Risk Probability Scatter Analysis"
                )
                fig_scatter.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_scatter, use_container_width=True)

            st.markdown("---")

            # Threshold Analysis Data Table from Saved Reports
            st.subheader("📋 Decision Boundary Threshold Analysis")
            th_path = registry.base_dir / "reports" / "model_reports" / "threshold_analysis.csv"
            if th_path.exists():
                df_th = pd.read_csv(th_path)
                st.dataframe(df_th, use_container_width=True, hide_index=True)
            else:
                st.info("Threshold analysis report not found.")

        finally:
            db.close()
    except Exception as e:
        st.error(f"⚠️ Unable to load risk score distributions from database: {e}")


if __name__ == "__main__":
    render_risk_analysis_page()
