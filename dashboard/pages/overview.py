"""
Streamlit Executive Overview Dashboard Page.
Hydrated with real data from database repository and Plotly charts.
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
import plotly.graph_objects as go
from src.database.connection import SessionLocal
from src.database.repository import TransactionRepository


def render_overview_page():
    """Renders Executive Overview Dashboard."""
    st.markdown(
        """
        <div class="main-header">
            <h1>📊 System Executive Overview</h1>
            <p>Real-time financial fraud monitoring, risk scoring distribution, and high-risk alerts.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        db = SessionLocal()
        try:
            repo = TransactionRepository(db)
            summary = repo.get_analytics_summary()
            ts_data = repo.get_time_series_analytics()
            recent_high_risk = repo.get_all(limit=10, risk_level="HIGH")

            # Top KPI Cards Row
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Transactions", f"{summary['total_transactions']:,}")
            with c2:
                st.metric("Fraud Detected", f"{summary['total_fraud_predictions']:,}", delta=f"{summary['fraud_rate_pct']:.1f}% Rate", delta_color="inverse")
            with c3:
                st.metric("High Risk Transactions", f"{summary['high_risk_count']:,}")
            with c4:
                st.metric("Total Processed Value", f"${summary['total_transaction_value']:,.2f}")

            st.markdown("---")

            # Analytics Charts Row
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("📈 Transaction & Fraud Volume Trend")
                if ts_data:
                    df_ts = pd.DataFrame(ts_data)
                    fig_ts = px.line(
                        df_ts,
                        x="date",
                        y=["total_count", "fraud_count"],
                        labels={"value": "Count", "date": "Date", "variable": "Metric"},
                        color_discrete_map={"total_count": "#38bdf8", "fraud_count": "#ef4444"},
                        title="Daily Transaction & Fraud Volume"
                    )
                    fig_ts.update_layout(template="plotly_dark", height=350)
                    st.plotly_chart(fig_ts, use_container_width=True)
                else:
                    st.info("No time-series records available.")

            with col_right:
                st.subheader("🎯 Risk Tier Breakdown")
                risk_counts = {
                    "Low Risk": summary["low_risk_count"],
                    "Medium Risk": summary["medium_risk_count"],
                    "High Risk": summary["high_risk_count"]
                }
                fig_pie = px.pie(
                    names=list(risk_counts.keys()),
                    values=list(risk_counts.values()),
                    color=list(risk_counts.keys()),
                    color_discrete_map={"Low Risk": "#22c55e", "Medium Risk": "#eab308", "High Risk": "#ef4444"},
                    hole=0.4,
                    title="Transaction Risk Tier Distribution"
                )
                fig_pie.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")

            # Recent High Risk Table
            st.subheader("🚨 Recent High-Risk Flagged Transactions")
            if recent_high_risk:
                records = []
                for tx in recent_high_risk:
                    records.append({
                        "Transaction ID": tx.transaction_id,
                        "Customer ID": tx.customer_id,
                        "Date": tx.transaction_date,
                        "Amount": f"${tx.transaction_amount:,.2f}",
                        "Category": tx.merchant_category,
                        "Payment Method": tx.payment_method,
                        "Fraud Prob": f"{tx.fraud_probability * 100:.1f}%" if tx.fraud_probability is not None else "N/A",
                        "Risk Score": f"{tx.risk_score:.1f}" if tx.risk_score is not None else "N/A",
                        "Risk Tier": tx.risk_level or "N/A"
                    })
                st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
            else:
                st.info("No high-risk transactions recorded.")

        finally:
            db.close()
    except Exception as e:
        st.error(f"⚠️ Unable to load dashboard metrics from database: {e}")


if __name__ == "__main__":
    render_overview_page()
