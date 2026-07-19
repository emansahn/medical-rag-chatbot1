"""About page — team, project context, architecture overview."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.frontend.components.icons import icon
from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.theme import apply_theme
from src.frontend.components.top_nav import render_top_nav


def main() -> None:
    apply_theme("À propos", "ℹ️")
    render_top_nav("a_propos")
    render_sidebar()

    st.markdown(
        f'<div class="mc-page-header"><div class="mc-eyebrow">{icon("info", 14)}À propos</div>'
        '<h1 class="mc-page-title">La technologie au service d’une information fiable.</h1>'
        '<div class="mc-page-lead">Un projet académique conçu pour faciliter l’accès à des '
        'informations médicales contextualisées au Maroc.</div></div>', unsafe_allow_html=True,
    )

    st.markdown(
        """
### Le contexte
Projet de fin de module — *Programmation Python Avancée*, AU 2025/2026
Université Chouaïb Doukkali, Faculté des Sciences, El Jadida.

L'accès à l'information médicale fiable reste limité pour une partie de la
population marocaine, notamment à cause de la barrière linguistique (Darija
vs. ressources officielles en français) et de la difficulté d'accès aux
professionnels de santé dans certaines régions. Ce chatbot vise à combler ce
manque en s'appuyant uniquement sur des **sources médicales marocaines
officielles**, via une architecture RAG (Retrieval-Augmented Generation).
"""
    )

    st.divider()
    st.markdown("### Équipe et répartition")

    modules = [
        ("database", "Extraction & Prétraitement", "Données brutes → chunks propres",
         "Collecte (PDF/web), extraction, nettoyage, chunking (300–800 tokens, overlap)."),
        ("search", "Indexation & Moteur RAG", "Le cœur du RAG",
         "Embeddings, base vectorielle (ChromaDB), recherche Top-K, prompt, génération LLM."),
        ("settings", "Application & Intégration", "Backend & frontend",
         "Backend FastAPI, frontend Streamlit, historique, sources, tests, documentation."),
    ]
    c1, c2, c3 = st.columns(3)
    for col, (icon_name, title, subtitle, copy) in zip((c1, c2, c3), modules):
        with col:
            st.markdown(
                f'<div class="mc-card"><div class="mc-card-icon">{icon(icon_name, 18)}</div>'
                f'<div class="mc-card-title">{title}</div>'
                f'<div style="font-weight:600;color:var(--mc-text);font-size:13px;margin-bottom:6px;">{subtitle}</div>'
                f'<div class="mc-card-copy">{copy}</div></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("### Architecture générale")
    steps = [
        "Utilisateur", "Darija→Français (optionnel)", "Embedding de la requête",
        "Recherche vectorielle", "Documents pertinents", "LLM + Contexte",
        "Réponse générée", "Génération en Darija (optionnel)",
    ]
    chevron = icon("chevron-right", 14, "mc-flow-arrow")
    flow_html = '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;">'
    for i, step in enumerate(steps):
        flow_html += f'<span class="mc-badge neutral">{step}</span>'
        if i < len(steps) - 1:
            flow_html += chevron
    flow_html += "</div>"
    st.markdown(flow_html, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Une expérience multilingue")
    st.markdown(
        f'<div class="mc-callout">{icon("globe", 18)}<div>'
        "Les documents sources sont en français ; les utilisateurs peuvent poser leur "
        "question en Darija marocaine. Approche : traduire la question vers le français, "
        "exécuter le RAG normalement, puis générer la réponse en Darija simple."
        "</div></div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
