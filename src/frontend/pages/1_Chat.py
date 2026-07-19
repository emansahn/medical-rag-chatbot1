"""Main chat page — the ChatGPT-like conversational interface."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.frontend.components.chat_bubble import render_message, render_typing_indicator
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


def _filtered_messages() -> list[dict]:
    query = st.session_state.get("history_search", "").strip().lower()
    if not query:
        return st.session_state.messages
    return [m for m in st.session_state.messages if query in m["content"].lower()]


def main() -> None:
    apply_theme("Chat", "💬")
    _init_session_state()
    render_top_nav("chat")
    render_sidebar()

    st.markdown(
        f'<div class="mc-page-header"><div class="mc-eyebrow">{icon("message-square", 14)}Conversation</div>'
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
                f'<div class="mc-chat-intro">{icon("send", 18)}<div>'
                "<strong>Commencez une conversation</strong>"
                "<span>Décrivez votre question clairement, sans partager de données personnelles sensibles.</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )
        for i, msg in enumerate(messages):
            render_message(
                msg["role"], msg["content"], msg.get("sources"),
                msg_index=i, language=msg.get("language", "fr"),
            )

    question = st.chat_input("Écrivez votre question médicale…")

    if question:
        selected_language = st.session_state.language
        st.session_state.messages.append(
            {"role": "user", "content": question, "sources": [], "language": selected_language}
        )

        with chat_container:
            render_message(
                "user", question, msg_index=len(st.session_state.messages),
                language=selected_language,
            )
            placeholder = st.empty()
            with placeholder:
                render_typing_indicator()

            client = get_backend_client()
            try:
                response = client.send_message(
                    question=question,
                    conversation_id=st.session_state.conversation_id,
                    language=selected_language,
                )
                st.session_state.conversation_id = response["conversation_id"]
                answer = response["answer"]
                sources = response.get("sources", [])

                placeholder.empty()
                render_message(
                    "assistant", answer, sources,
                    msg_index=len(st.session_state.messages) + 1,
                    language=selected_language,
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources, "language": selected_language}
                )

            except ApiError as exc:
                placeholder.empty()
                st.error(f"Erreur : {exc.message}")


if __name__ == "__main__":
    main()
