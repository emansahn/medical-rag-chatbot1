"""Settings page — response language, model selector (placeholder), backend config check."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.theme import apply_theme
from src.frontend.services.api_client import ApiError, get_backend_client


def main() -> None:
    apply_theme("Paramètres", "⚙️")
    render_sidebar()

    st.markdown('<div class="mc-app-title" style="font-size:1.8rem;">⚙️ Paramètres</div>', unsafe_allow_html=True)

    st.markdown("### Préférences de réponse")
    st.session_state.language = st.radio(
        "Langue de réponse",
        options=["fr", "ary"],
        format_func=lambda x: "Français" if x == "fr" else "Darija marocaine (bonus)",
        index=0 if st.session_state.get("language", "fr") == "fr" else 1,
        horizontal=True,
    )

    st.markdown("### Modèle de langage (LLM)")
    st.info("🔧 Le choix du modèle sera activé une fois le moteur RAG de la Personne 2 branché.")
    st.selectbox(
        "Modèle",
        options=["stub (démo)", "gpt-4o-mini", "llama-3 (Ollama, local)"],
        disabled=True,
    )

    st.divider()
    st.markdown("### Configuration du backend")
    client = get_backend_client()
    try:
        config = client.public_config()
        st.json(config)
    except ApiError as exc:
        st.error(f"Impossible de charger la configuration : {exc.message}")

    st.divider()
    if st.button("🗑️ Réinitialiser toute la session"):
        for key in ["messages", "conversation_id", "history_search"]:
            st.session_state.pop(key, None)
        st.success("Session réinitialisée.")
        st.rerun()


if __name__ == "__main__":
    main()
