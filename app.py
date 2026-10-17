"""Standalone Streamlit application for the z/OS MVS learning lab."""

import streamlit as st

from zos_learning_lab import render_learning_lab


st.set_page_config(
    page_title="MVS SYSPROG Learning Lab",
    page_icon="🖥️",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"], [data-testid="stAppViewContainer"] {
        font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
    }
    .stApp { background: #f4f4f4; color: #161616; }
    [data-testid="stSidebar"] { background: #ffffff; }
    .block-container { max-width: 1400px; padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

render_learning_lab()
