"""Structured Finance Surveillance dashboard entry point."""

import streamlit as st

st.set_page_config(
    page_title="Structured Finance Surveillance",
    page_icon="📊",
    layout="wide",
)


pages = {
    "Surveillance": [
        st.Page(
            "pages/executive_overview.py",
            title="Executive Overview",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "pages/credit_performance.py",
            title="Credit Performance",
            icon=":material/trending_up:",
        ),
        st.Page(
            "pages/underwriting_risk.py",
            title="Underwriting Risk",
            icon=":material/analytics:",
        ),
        st.Page(
            "pages/vintage_analysis.py",
            title="Vintage Analysis",
            icon=":material/timeline:",
        ),
        st.Page(
            "pages/data_quality.py",
            title="Data Quality & Controls",
            icon=":material/verified:",
        ),
    ],
}


navigation = st.navigation(pages)

navigation.run()
