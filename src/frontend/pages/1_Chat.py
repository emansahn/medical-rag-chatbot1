"""Main chat page — the ChatGPT-like conversational interface."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.frontend.components.chat_bubble import render_message, render_typing_indicator
from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.theme import apply_theme
from src.frontend.services.api_client import ApiError, get_backend_client


def _init_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("conversation_id", None)
    st.session_state.setdefault("language", "fr")
    st.session_state.setdefault("history_search", "")


def _filtered_messages() -> list[dict]:
    query = st.session_state.get("history_search", "").strip().lower()
    if not query:
        return st.session_state.messages
    return [m for m in st.session_state.messages if query in m["content"].lower()]


def main() -> None:
    apply_theme("Chat", "💬")
    _init_session_state()
    render_sidebar()

    st.markdown(
        '<div class="mc-page-header"><div class="mc-eyebrow">Conversation</div>'
        '<h1 class="mc-page-title">Comment puis-je vous aider ?</h1>'
        '<div class="mc-page-lead">Les réponses s’appuient sur les sources médicales '
        'marocaines officielles disponibles dans la base documentaire.</div></div>',
        unsafe_allow_html=True,
    )

    chat_container = st.container()
    with chat_container:
        messages = _filtered_messages()
        if not messages:
            st.markdown(
                '<div class="mc-chat-intro"><strong>Commencez une conversation</strong>'
                '<span>Décrivez votre question clairement, sans partager de données personnelles sensibles.</span></div>',
                unsafe_allow_html=True,
            )
        for i, msg in enumerate(messages):
            render_message(msg["role"], msg["content"], msg.get("sources"), msg_index=i)

    question = st.chat_input("Écrivez votre question médicale…")

    if question:
        st.session_state.messages.append({"role": "user", "content": question, "sources": []})

        with chat_container:
            render_message("user", question, msg_index=len(st.session_state.messages))
            placeholder = st.empty()
            with placeholder:
                render_typing_indicator()

            client = get_backend_client()
            try:
                response = client.send_message(
                    question=question,
                    conversation_id=st.session_state.conversation_id,
                    language=st.session_state.language,
                )
                st.session_state.conversation_id = response["conversation_id"]
                answer = response["answer"]
                sources = response.get("sources", [])

                if response.get("is_stub"):
                    st.toast("Mode démo : le moteur RAG réel n'est pas encore branché.", icon="⚠️")

                placeholder.empty()
                render_message("assistant", answer, sources, msg_index=len(st.session_state.messages) + 1)
                st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})

            except ApiError as exc:
                placeholder.empty()
                st.error(f"Erreur : {exc.message}")


if __name__ == "__main__":
    main()
