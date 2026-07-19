"""Horizontal top navigation, replacing Streamlit's default vertical page list.

Which item is "active" is passed explicitly by the calling page rather than
inferred from Streamlit's client-side routing state (not reliably
inspectable from custom CSS — see the note in assets/style.css).
"""
import streamlit as st

NAV_ITEMS = [
    ("accueil", "Accueil", "app.py"),
    ("chat", "Chat", "pages/1_Chat.py"),
    ("parametres", "Paramètres", "pages/3_Settings.py"),
    ("a_propos", "À propos", "pages/2_About.py"),
    ("glossaire", "Glossaire", "pages/4_Glossary_Admin.py"),
]


def render_top_nav(active: str) -> None:
    cols = st.columns([1] * len(NAV_ITEMS) + [4])
    for col, (key, label, target) in zip(cols, NAV_ITEMS):
        with col:
            if key == active:
                st.markdown(f'<span class="mc-nav-active">{label}</span>', unsafe_allow_html=True)
            else:
                st.page_link(target, label=label)
    st.divider()
