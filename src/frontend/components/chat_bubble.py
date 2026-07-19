"""Renders chat messages as styled bubbles with markdown, sources, and a copy button."""
import streamlit as st


def render_message(
    role: str,
    content: str,
    sources: list[dict] | None = None,
    msg_index: int = 0,
    language: str = "fr",
) -> None:
    """Render a single chat message bubble.

    Args:
        role: "user" or "assistant".
        content: Markdown-formatted message text.
        sources: Optional list of {"title", "url", "excerpt"} citations.
        msg_index: Index used to give Streamlit widgets unique keys.
    """
    is_user = role == "user"
    label = "Vous" if is_user else "Assistant médical"
    script_class = " darija-arabic" if language == "ary-arab" else ""

    st.markdown(
        f'<div class="mc-bubble-row {role}"><div class="mc-message">'
        f'<div class="mc-role-label">{label}</div>'
        f'<div class="mc-bubble {role}{script_class}">{content}</div></div></div>',
        unsafe_allow_html=True,
    )

    if sources:
        with st.expander(f"Sources consultées ({len(sources)})", expanded=False):
            for src in sources:
                st.markdown(
                    f'<span class="mc-source-chip">{src["title"]}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(src.get("excerpt", ""))
                if src.get("url"):
                    st.markdown(f"[Voir la source]({src['url']})")


def render_typing_indicator() -> None:
    st.markdown(
        '<div class="mc-typing"><span></span><span></span><span></span></div>',
        unsafe_allow_html=True,
    )
