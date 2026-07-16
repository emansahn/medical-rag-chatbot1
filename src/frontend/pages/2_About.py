"""About page — team, project context, architecture overview."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.theme import apply_theme


def main() -> None:
    apply_theme("À propos", "ℹ️")
    render_sidebar()

    st.markdown('<div class="mc-app-title" style="font-size:1.8rem;">ℹ️ À propos du projet</div>', unsafe_allow_html=True)

    st.markdown(
        """
### Contexte
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
    st.markdown("### 👥 Équipe & répartition")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 📂 Personne 1")
        st.markdown("**Données & prétraitement**")
        st.write("Collecte (PDF/web), extraction, nettoyage, chunking (300–800 tokens, overlap).")
    with c2:
        st.markdown("#### 🧠 Personne 2")
        st.markdown("**Indexation & moteur RAG**")
        st.write("Embeddings, base vectorielle (FAISS/ChromaDB), recherche Top-K, prompt, génération LLM.")
    with c3:
        st.markdown("#### 💻 Personne 3")
        st.markdown("**Application & intégration**")
        st.write("Backend FastAPI, frontend Streamlit, historique, sources, tests, documentation.")

    st.divider()
    st.markdown("### 🏗️ Architecture générale")
    st.markdown(
        "`Utilisateur → (Darija→Français, optionnel) → Embedding de la requête → "
        "Recherche vectorielle → Documents pertinents → LLM + Contexte → "
        "Réponse générée → (Génération en Darija, optionnel)`"
    )

    st.divider()
    st.markdown("### 🌍 Bonus multilingue")
    st.write(
        "Les documents sources sont en français ; les utilisateurs peuvent poser leur "
        "question en Darija marocaine. Approche : traduire la question vers le français, "
        "exécuter le RAG normalement, puis générer la réponse en Darija simple."
    )


if __name__ == "__main__":
    main()
