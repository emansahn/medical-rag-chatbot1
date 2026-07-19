"""
Streamlit entrypoint — Home page.

Run with:
    streamlit run src/frontend/app.py
"""
import sys
from pathlib import Path

# `streamlit run` does NOT add the project root to sys.path the way
# `python -m` does, so `from src...` imports fail unless PYTHONPATH is set
# manually. Adding the root here makes the app work out of the box on any
# OS/shell, with no environment variable required.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from src.frontend.components.icons import icon
from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.theme import apply_theme
from src.frontend.components.top_nav import render_top_nav
from src.frontend.services.api_client import ApiError, get_backend_client


def _init_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("conversation_id", None)
    st.session_state.setdefault("language", "fr")
    st.session_state.setdefault("history_search", "")


def main() -> None:
    apply_theme("Accueil", "🏠")
    _init_session_state()
    render_top_nav("accueil")
    render_sidebar()

    st.markdown(
        f'<div class="mc-page-header"><div class="mc-eyebrow">{icon("activity", 14)}Assistant médical intelligent</div>'
        '<h1 class="mc-page-title">Une information médicale fiable, simplement.</h1>'
        '<div class="mc-page-lead">Posez vos questions de santé et obtenez des réponses '
        'contextualisées à partir de sources médicales marocaines officielles.</div></div>',
        unsafe_allow_html=True,
    )

    cards = [
        ("message-square", "Poser une question", "Échangez avec l’assistant et consultez les sources utilisées."),
        ("settings", "Personnaliser", "Choisissez votre langue et adaptez les préférences de réponse."),
        ("info", "Comprendre le projet", "Découvrez les sources, l’architecture RAG et l’équipe."),
    ]
    col1, col2, col3 = st.columns(3)
    for col, (icon_name, title, copy) in zip((col1, col2, col3), cards):
        with col:
            st.markdown(
                f'<div class="mc-card interactive"><div class="mc-card-icon">{icon(icon_name, 18)}</div>'
                f'<div class="mc-card-title">{title}</div><div class="mc-card-copy">{copy}</div></div>',
                unsafe_allow_html=True,
            )
    with col1:
        st.page_link("pages/1_Chat.py", label="Ouvrir le chat")
    with col2:
        st.page_link("pages/3_Settings.py", label="Voir les paramètres")
    with col3:
        st.page_link("pages/2_About.py", label="En savoir plus")

    st.divider()
    st.markdown("### Disponibilité du service")
    client = get_backend_client()
    try:
        status = client.status()
        health = client.health()
        stats = [
            ("shield", health.get("status") == "ok", "API", "En ligne" if health.get("status") == "ok" else "Indisponible"),
            ("activity", status.get("rag_engine_ready"), "Moteur RAG", "Actif" if status.get("rag_engine_ready") else "Indisponible"),
            ("globe", status.get("darija_support_enabled"), "Darija", "Disponible" if status.get("darija_support_enabled") else "Non disponible"),
        ]
        stat_html = '<div class="mc-stat-row">'
        for icon_name, ok, label, value in stats:
            state = "ok" if ok else "warn"
            stat_html += (
                f'<div class="mc-stat"><div class="mc-stat-icon {state}">{icon(icon_name, 18)}</div>'
                f'<div><div class="mc-stat-value">{value}</div><div class="mc-stat-label">{label}</div></div></div>'
            )
        stat_html += "</div>"
        st.markdown(stat_html, unsafe_allow_html=True)
    except ApiError as exc:
        st.error(f"Impossible de contacter le backend : {exc.message}")
        st.info("Démarrez l'API avec : `uvicorn src.backend.main:app --reload --port 8000`")

    st.divider()
    st.markdown(
        f'<div class="mc-callout">{icon("alert-triangle", 18)}<div><strong>Information importante</strong><br>'
        'Cette application fournit des informations générales et ne remplace ni un diagnostic '
        'ni un avis médical professionnel. En cas d’urgence, contactez les services de santé.</div></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
