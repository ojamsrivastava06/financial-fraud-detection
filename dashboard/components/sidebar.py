"""
Sidebar Navigation Component.
"""

import streamlit as st


from src.database.connection import SessionLocal
from src.models.model_registry import ModelRegistry
from sqlalchemy import text


def render_sidebar_status():
    """
    Renders live system status indicators (Database & ML Model).
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")

    # Live Health Checks
    db_connected = False
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_connected = True
        finally:
            db.close()
    except Exception:
        db_connected = False

    try:
        registry = ModelRegistry()
        model, _, metadata = registry.load_active_model()
        model_loaded = model is not None
        model_name = metadata.get("model_name", "None") if metadata else "None"
        model_version = metadata.get("model_version", "1.0.0") if metadata else "1.0.0"
    except Exception:
        model_loaded = False
        model_name = "None"
        model_version = "None"

    if db_connected:
        st.sidebar.success("Database: Connected")
    else:
        st.sidebar.error("Database: Offline")

    if model_loaded:
        st.sidebar.success(f"Model: {model_name} (v{model_version})")
    else:
        st.sidebar.warning("Model: Not Loaded")


def render_sidebar():
    """
    Renders sidebar title, navigation options, and live system status indicators.
    """
    st.sidebar.title("🛡️ Fraud Guard AI")
    st.sidebar.caption("Financial Fraud Detection Platform v1.0.0")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        options=[
            "Overview",
            "Transactions",
            "Fraud Analysis",
            "Risk Analysis",
            "Alerts",
            "Model Performance",
        ],
        index=0,
    )

    render_sidebar_status()
    return page
