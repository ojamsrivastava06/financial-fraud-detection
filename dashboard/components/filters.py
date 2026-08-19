"""
Filter controls UI component skeleton.
"""

import streamlit as st


def render_filter_bar():
    """
    Renders filter controls container (Date Range, Risk Tier, Merchant, Amount Range).
    """
    with st.expander("🔍 Filter & Search Criteria", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("Risk Level", ["All", "High Risk", "Medium Risk", "Low Risk"], disabled=True)
        with col2:
            st.selectbox("Payment Method", ["All", "Credit Card", "Debit Card", "NetBanking", "PayPal"], disabled=True)
        with col3:
            st.text_input("Customer ID / Transaction ID", placeholder="Search...", disabled=True)
        st.caption("Filters will be activated once database seeding is executed (Phase 4).")
