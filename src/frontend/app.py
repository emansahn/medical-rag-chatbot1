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

from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.theme import apply_theme
from src.frontend.services.api_client import ApiError, get_backend_client


def _init_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("conversation_id", None)
    st.session_state.setdefault("language", "fr")
    st.session_state.setdefault("history_search", "")


def main() -> None:
    apply_theme("Accueil", "🏠")
    _init_session_state()
    render_sidebar()

    st.markdown('<div class="mc-app-title" style="font-size:2.2rem;">🩺 Medical RAG Chatbot</div>', unsafe_allow_html=True)
    st.subheader("Chatbot médical intelligent basé sur RAG, adapté au contexte marocain")

    st.write(
        "Cette application répond à des questions médicales générales en s'appuyant "
        "**uniquement sur des sources médicales marocaines officielles** "
        "(Ministère de la Santé, OMS Maroc, CHU, guides cliniques), afin de limiter "
        "les hallucinations et de fournir des réponses fiables et contextualisées."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 💬 Chat")
        st.write("Posez une question médicale et obtenez une réponse sourcée.")
        st.page_link("pages/1_Chat.py", label="Ouvrir le chat →", icon="💬")
    with col2:
        st.markdown("#### ⚙️ Paramètres")
        st.write("Langue de réponse, préférences d'affichage.")
        st.page_link("pages/3_Settings.py", label="Ouvrir les paramètres →", icon="⚙️")
    with col3:
        st.markdown("#### ℹ️ À propos")
        st.write("Équipe, architecture, avancement du projet.")
        st.page_link("pages/2_About.py", label="En savoir plus →", icon="ℹ️")

    st.divider()
    st.markdown("### État du système")
    client = get_backend_client()
    try:
        status = client.status()
        health = client.health()
        c1, c2, c3 = st.columns(3)
        c1.metric("API Backend", "En ligne ✅" if health.get("status") == "ok" else "Erreur")
        c2.metric("Moteur RAG", "Actif" if status.get("rag_engine_ready") else "Mode démo")
        c3.metric("Support Darija", "Activé" if status.get("darija_support_enabled") else "Désactivé")
    except ApiError as exc:
        st.error(f"Impossible de contacter le backend : {exc.message}")
        st.info("Démarrez l'API avec : `uvicorn src.backend.main:app --reload --port 8000`")

    st.divider()
    st.caption(
        "⚠️ Avertissement médical : cette application est un projet académique et ne "
        "remplace en aucun cas un diagnostic ou un avis médical professionnel. En cas "
        "d'urgence, contactez immédiatement les services de santé."
    )


if __name__ == "__main__":
    main()
