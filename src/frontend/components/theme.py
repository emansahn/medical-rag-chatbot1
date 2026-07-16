"""Applies the shared dark medical theme to every Streamlit page."""
from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def apply_theme(page_title: str, page_icon: str = "🩺") -> None:
    """Set page config and inject the custom CSS. Call first, on every page."""
    st.set_page_config(
        page_title=f"{page_title} · Medical RAG",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if _CSS_PATH.exists():
        st.markdown(f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
