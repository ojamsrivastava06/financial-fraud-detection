"""
Streamlit Live Security Alert Management Dashboard Page.
Hydrated with real security alerts from SQLite DB with status update workflows.
"""

from pathlib import Path
import sys

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from src.database.connection import SessionLocal
from src.database.repository import AlertRepository


def render_alerts_page():
    """Renders Real-time Security Alert Management Queue & Workflow Page."""
    st.markdown(
        """
        <div class="main-header">
            <h1>🚨 Security Alert Management Queue</h1>
            <p>Real-time high-risk transaction alerts, review workflow, and resolution status management.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        db = SessionLocal()
        try:
            repo = AlertRepository(db)

            # Filters
            c1, c2 = st.columns(2)
            with c1:
                status_filter = st.selectbox("Alert Status", ["All", "OPEN", "INVESTIGATING", "RESOLVED", "DISMISSED"])
            with c2:
                severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM"])

            st_val = None if status_filter == "All" else status_filter
            sev_val = None if severity_filter == "All" else severity_filter

            alerts = repo.get_all_alerts(status=st_val, severity=sev_val, limit=100)
            total_alerts = repo.count(status=st_val, severity=sev_val)

            st.caption(f"Showing {len(alerts)} of {total_alerts} matching security alerts")

            if alerts:
                display_records = []
                for a in alerts:
                    display_records.append({
                        "Alert ID": a.id,
                        "Transaction ID": a.transaction_id,
                        "Severity": a.severity,
                        "Fraud Prob": f"{a.fraud_probability * 100:.1f}%",
                        "Risk Score": f"{a.risk_score:.1f}",
                        "Status": a.status,
                        "Created At": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "N/A",
                        "Message": a.message
                    })

                st.dataframe(pd.DataFrame(display_records), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("🛠️ Take Action on Security Alert")

                alert_ids = [a.id for a in alerts]
                selected_alert_id = st.selectbox("Select Alert ID to manage:", alert_ids)

                selected_alert = repo.get_by_id(selected_alert_id)
                if selected_alert:
                    st.info(f"**Alert #{selected_alert.id}** for Transaction `{selected_alert.transaction_id}` | Severity: **{selected_alert.severity}** | Status: **{selected_alert.status}**")
                    st.write(f"**Message:** {selected_alert.message}")

                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    notes_input = st.text_input("Resolution Notes (Optional):", placeholder="e.g. Verified with cardholder via SMS")

                    with col_btn1:
                        if st.button("🔍 Mark Investigating"):
                            repo.update_status(selected_alert.id, "INVESTIGATING", notes_input)
                            st.success(f"Alert #{selected_alert.id} status updated to INVESTIGATING.")
                            st.rerun()

                    with col_btn2:
                        if st.button("✅ Mark Resolved"):
                            repo.update_status(selected_alert.id, "RESOLVED", notes_input)
                            st.success(f"Alert #{selected_alert.id} status updated to RESOLVED.")
                            st.rerun()

                    with col_btn3:
                        if st.button("🚫 Mark Dismissed"):
                            repo.update_status(selected_alert.id, "DISMISSED", notes_input)
                            st.warning(f"Alert #{selected_alert.id} status updated to DISMISSED.")
                            st.rerun()
            else:
                st.info("No security alerts match the selected status and severity criteria.")

        finally:
            db.close()
    except Exception as e:
        st.error(f"⚠️ Unable to query security alerts from database: {e}")


if __name__ == "__main__":
    render_alerts_page()
