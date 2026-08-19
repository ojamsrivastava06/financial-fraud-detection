"""
KPI Cards visual component renderer.
"""

import streamlit as st


def render_kpi_placeholder(title: str, subtitle: str = "Awaiting Pipeline"):
    """
    Renders KPI card placeholder without hardcoded fake numbers.
    """
    st.markdown(
        f"""
        <div class="status-card">
            <h4>{title}</h4>
            <div class="status-value">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
