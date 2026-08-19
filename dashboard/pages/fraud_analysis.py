"""
Streamlit Fraud Pattern Analysis Dashboard Page.
Hydrated with real database metrics and Plotly risk breakdowns.
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


def render_fraud_analysis_page():
    """Renders Granular Fraud Pattern Analysis Page."""
    st.markdown(
        """
        <div class="main-header">
            <h1>🔍 Fraud Pattern & Anomaly Breakdown</h1>
            <p>Categorical breakdown of fraud rates across merchants, payment instruments, devices, and geographic origin.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        db = SessionLocal()
        try:
            # Load transactions into DataFrame using standard SQLAlchemy text clause
            query_sql = text("SELECT * FROM transactions")
            df = pd.read_sql(query_sql, db.bind)

            if df.empty:
                st.info("No transaction data available for analysis.")
                return

            # Clean and fill any potential missing values for reliable grouping
            df["fraud_prediction"] = df["fraud_prediction"].fillna(0)
            df["merchant_category"] = df["merchant_category"].fillna("Unknown")
            df["payment_method"] = df["payment_method"].fillna("Unknown")
            df["device_type"] = df["device_type"].fillna("Unknown")
            df["is_international"] = df["is_international"].fillna(0).astype(int)
            df["location"] = df["location"].fillna("Unknown")
            df["risk_score"] = df["risk_score"].fillna(0.0)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🛍️ Fraud Rate by Merchant Category")
                cat_df = df.groupby("merchant_category")["fraud_prediction"].mean().reset_index()
                cat_df["fraud_rate_pct"] = cat_df["fraud_prediction"] * 100
                fig_cat = px.bar(
                    cat_df,
                    x="merchant_category",
                    y="fraud_rate_pct",
                    labels={"merchant_category": "Merchant Category", "fraud_rate_pct": "Predicted Fraud Rate (%)"},
                    color="fraud_rate_pct",
                    color_continuous_scale="Reds"
                )
                fig_cat.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_cat, use_container_width=True)

            with col2:
                st.subheader("💳 Fraud Rate by Payment Method")
                pm_df = df.groupby("payment_method")["fraud_prediction"].mean().reset_index()
                pm_df["fraud_rate_pct"] = pm_df["fraud_prediction"] * 100
                fig_pm = px.bar(
                    pm_df,
                    x="payment_method",
                    y="fraud_rate_pct",
                    labels={"payment_method": "Payment Instrument", "fraud_rate_pct": "Predicted Fraud Rate (%)"},
                    color="fraud_rate_pct",
                    color_continuous_scale="Purples"
                )
                fig_pm.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_pm, use_container_width=True)

            st.markdown("---")

            col3, col4 = st.columns(2)

            with col3:
                st.subheader("📱 Fraud by Device Platform")
                dev_df = df.groupby("device_type")["fraud_prediction"].sum().reset_index()
                fig_dev = px.pie(
                    dev_df,
                    names="device_type",
                    values="fraud_prediction",
                    title="Fraud Count by Client Device Type",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_dev.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_dev, use_container_width=True)

            with col4:
                st.subheader("🌐 International vs Domestic Fraud Rate")
                intl_df = df.groupby("is_international")["fraud_prediction"].mean().reset_index()
                intl_df["Type"] = intl_df["is_international"].map({0: "Domestic", 1: "International"})
                intl_df["fraud_rate_pct"] = intl_df["fraud_prediction"] * 100
                fig_intl = px.bar(
                    intl_df,
                    x="Type",
                    y="fraud_rate_pct",
                    labels={"Type": "Transaction Scope", "fraud_rate_pct": "Predicted Fraud Rate (%)"},
                    color="Type",
                    color_discrete_map={"Domestic": "#38bdf8", "International": "#ef4444"}
                )
                fig_intl.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_intl, use_container_width=True)

            st.markdown("---")
            st.subheader("📍 Geographic Location Risk Heatmap")
            loc_df = df.groupby("location").agg(
                total_count=("id", "count"),
                fraud_count=("fraud_prediction", "sum"),
                avg_risk_score=("risk_score", "mean")
            ).reset_index()
            loc_df["fraud_rate_pct"] = (loc_df["fraud_count"] / loc_df["total_count"]) * 100

            st.dataframe(loc_df, use_container_width=True, hide_index=True)

        finally:
            db.close()
    except Exception as e:
        st.error(f"⚠️ Unable to load fraud pattern analytics from database: {e}")


if __name__ == "__main__":
    render_fraud_analysis_page()
