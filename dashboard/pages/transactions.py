"""
Streamlit Transactions Explorer Dashboard Page.
Hydrated with real searchable & filterable transaction data from SQLite DB repository.
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
from src.database.repository import TransactionRepository


def render_transactions_page():
    """Renders Transaction Search, Filter, and Detail Explorer Page."""
    st.markdown(
        """
        <div class="main-header">
            <h1>💳 Transaction Explorer</h1>
            <p>Search, filter, and inspect granular financial transactions and model risk scores.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        db = SessionLocal()
        try:
            repo = TransactionRepository(db)

            # Filters Controls Section
            with st.expander("🔍 Search & Filter Controls", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    search = st.text_input("Search ID / Customer", placeholder="e.g. T100000 or CUST3252")
                with col2:
                    risk_filter = st.selectbox("Risk Level", ["All", "HIGH", "MEDIUM", "LOW"])
                with col3:
                    category_filter = st.selectbox("Merchant Category", ["All", "Travel", "Utilities", "Entertainment", "Health", "Fashion", "Grocery", "Food", "Electronics"])
                with col4:
                    fraud_only = st.checkbox("Predicted Fraud Only", value=False)

            # Map filter selections
            risk_sel = None if risk_filter == "All" else risk_filter
            cat_sel = None if category_filter == "All" else category_filter
            search_val = search.strip() if search else None

            # Fetch records
            tx_list = repo.get_all(
                limit=200,
                search=search_val,
                fraud_only=fraud_only,
                risk_level=risk_sel,
                merchant_category=cat_sel
            )
            total_count = repo.count(
                search=search_val,
                fraud_only=fraud_only,
                risk_level=risk_sel,
                merchant_category=cat_sel
            )

            st.caption(f"Showing {len(tx_list)} of {total_count} matching records")

            if tx_list:
                display_data = []
                for tx in tx_list:
                    display_data.append({
                        "Transaction ID": tx.transaction_id,
                        "Customer ID": tx.customer_id,
                        "Date": tx.transaction_date,
                        "Amount": f"${tx.transaction_amount:,.2f}",
                        "Category": tx.merchant_category,
                        "Payment Method": tx.payment_method,
                        "Device": tx.device_type,
                        "Location": tx.location,
                        "International": "Yes" if tx.is_international else "No",
                        "Fraud Prob": f"{tx.fraud_probability * 100:.1f}%" if tx.fraud_probability is not None else "N/A",
                        "Risk Score": f"{tx.risk_score:.1f}" if tx.risk_score is not None else "N/A",
                        "Risk Level": tx.risk_level or "N/A"
                    })

                st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

                # Granular Inspector
                st.markdown("---")
                st.subheader("🔍 Inspect Transaction Details")
                selected_tx_id = st.selectbox("Select Transaction ID to inspect:", [t.transaction_id for t in tx_list])

                tx_obj = repo.get_by_transaction_id(selected_tx_id)
                if tx_obj:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"**Transaction ID:** `{tx_obj.transaction_id}`")
                        st.write(f"**Customer ID:** `{tx_obj.customer_id}`")
                        st.write(f"**Date:** {tx_obj.transaction_date}")
                        st.write(f"**Amount:** ${tx_obj.transaction_amount:,.2f}")
                    with c2:
                        st.write(f"**Merchant Category:** {tx_obj.merchant_category}")
                        st.write(f"**Payment Method:** {tx_obj.payment_method}")
                        st.write(f"**Device:** {tx_obj.device_type}")
                        st.write(f"**Location:** {tx_obj.location}")
                    with c3:
                        st.write(f"**Fraud Probability:** `{tx_obj.fraud_probability * 100:.2f}%`" if tx_obj.fraud_probability is not None else "**Fraud Probability:** `N/A`")
                        st.write(f"**Risk Score:** `{tx_obj.risk_score:.1f}`" if tx_obj.risk_score is not None else "**Risk Score:** `N/A`")
                        st.write(f"**Risk Tier:** `{tx_obj.risk_level or 'N/A'}`")
                        st.write(f"**Ground Truth Target:** `{tx_obj.fraudulent if tx_obj.fraudulent is not None else 'N/A'}`")
            else:
                st.warning("No transactions match the selected filters.")

        finally:
            db.close()
    except Exception as e:
        st.error(f"⚠️ Unable to query transactions from database: {e}")


if __name__ == "__main__":
    render_transactions_page()
