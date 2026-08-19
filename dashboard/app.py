"""
Streamlit Interactive Dashboard Main Application Shell.
"""

from pathlib import Path
import streamlit as st
import sys

# Ensure root workspace directory is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dashboard.components.sidebar import render_sidebar_status
from dashboard.pages.overview import render_overview_page
from dashboard.pages.transactions import render_transactions_page
from dashboard.pages.fraud_analysis import render_fraud_analysis_page
from dashboard.pages.risk_analysis import render_risk_analysis_page
from dashboard.pages.alerts import render_alerts_page
from dashboard.pages.model_performance import render_model_performance_page

# Configure Streamlit page options
st.set_page_config(
    page_title="Fraud Guard AI Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS custom styles
css_file = ROOT_DIR / "dashboard" / "assets" / "styles" / "style.css"
if css_file.exists():
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Define native pages for seamless multipage navigation
pages = [
    st.Page(render_overview_page, title="Overview", icon="📊", default=True, url_path="overview"),
    st.Page(render_transactions_page, title="Transactions", icon="💳", url_path="transactions"),
    st.Page(render_fraud_analysis_page, title="Fraud Analysis", icon="🔍", url_path="fraud-analysis"),
    st.Page(render_risk_analysis_page, title="Risk Analysis", icon="⚖️", url_path="risk-analysis"),
    st.Page(render_alerts_page, title="Alerts", icon="🚨", url_path="alerts"),
    st.Page(render_model_performance_page, title="Model Performance", icon="🎯", url_path="model-performance"),
]

st.sidebar.title("🛡️ Fraud Guard AI")
st.sidebar.caption("Financial Fraud Detection Platform v1.0.0")

pg = st.navigation(pages)
render_sidebar_status()
pg.run()
