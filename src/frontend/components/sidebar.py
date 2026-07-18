"""Shared sidebar: branding, engine status, conversation controls, navigation."""
import streamlit as st

from src.frontend.services.api_client import ApiError, get_backend_client


def render_sidebar() -> None:
    client = get_backend_client()

    with st.sidebar:
        st.markdown(
            '<div class="mc-brand"><div class="mc-brand-mark">+</div>'
            '<div><div class="mc-brand-name">Medical RAG</div>'
            '<div class="mc-brand-subtitle">Assistant médical marocain</div></div></div>',
            unsafe_allow_html=True,
        )
        st.divider()

        _render_engine_status(client)
        st.divider()

        st.markdown('<div class="mc-section-label">Conversation</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Effacer", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.rerun()
        with col2:
            _render_export_button()

        search = st.text_input("Rechercher", placeholder="Rechercher dans l’historique…")
        if search:
            st.session_state.history_search = search
        else:
            st.session_state.history_search = ""

        st.divider()
        st.markdown('<div class="mc-section-label">Langue de réponse</div>', unsafe_allow_html=True)
        st.session_state.language = st.selectbox(
            "Langue", options=["fr", "ary"], format_func=lambda x: "Français" if x == "fr" else "Darija (bonus)",
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown('<div class="mc-section-label">Modèle</div>', unsafe_allow_html=True)
        st.selectbox(
            "Modèle LLM",
            options=["stub (démo)", "gpt-4o-mini (bientôt)", "llama-3-ollama (bientôt)"],
            disabled=True,
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("Information générale uniquement. Ne remplace pas un avis médical professionnel.")


def _render_engine_status(client) -> None:
    try:
        status = client.status()
        ready = status.get("rag_engine_ready", False)
        badge_class = "ok" if ready else "warn"
        badge_text = "Moteur RAG actif" if ready else "Mode démo (mock)"
        st.markdown(f'<span class="mc-badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)
        st.caption(
            f"RAG: {status.get('rag_mode')} · Data: {status.get('data_mode')} · "
            f"Chunks: {status.get('chunks_indexed')}"
        )
    except ApiError:
        st.markdown('<span class="mc-badge error">Backend hors-ligne</span>', unsafe_allow_html=True)
        st.caption("Démarrez l'API : `uvicorn src.backend.main:app --reload`")


def _render_export_button() -> None:
    messages = st.session_state.get("messages", [])
    if not messages:
        st.button("Exporter", use_container_width=True, disabled=True)
        return

    lines = []
    for m in messages:
        role = "Utilisateur" if m["role"] == "user" else "Assistant"
        lines.append(f"### {role}\n{m['content']}\n")
    export_text = "\n".join(lines)

    st.download_button(
        "Exporter",
        data=export_text,
        file_name="conversation_medical_rag.md",
        mime="text/markdown",
        use_container_width=True,
    )
