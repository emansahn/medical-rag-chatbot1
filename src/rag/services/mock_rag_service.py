"""
MockRAGService — dependency-free stand-in for the real RAG engine.

Imports NOTHING from FAISS/ChromaDB/LangChain/sentence-transformers, on
purpose: this file is what lets Person 3 (and Person 1) run the entire
application without installing `requirements/person2-rag.txt`.

It returns realistic-looking, clearly-labeled fake answers with fake source
citations pulled from a small canned knowledge base, so the chat UX
(bubbles, sources panel, typing indicator, exports...) can be built and
demoed convincingly before the real engine exists.
"""
import random
from typing import List

from src.core.logging_config import get_logger
from src.rag.interfaces.rag_service_interface import RAGAnswer, RAGService, SourceCitation

logger = get_logger(__name__)

_MOCK_KNOWLEDGE_BASE: List[SourceCitation] = [
    SourceCitation(
        title="Guide de prévention du diabète — Ministère de la Santé",
        url="https://www.sante.gov.ma/",
        excerpt="Exemple de source simulée : recommandations sur le dépistage et la prévention du diabète de type 2.",
    ),
    SourceCitation(
        title="Campagne nationale de vaccination — OMS Maroc",
        url="https://www.emro.who.int/countries/mar/",
        excerpt="Exemple de source simulée : calendrier vaccinal recommandé et sensibilisation du public.",
    ),
    SourceCitation(
        title="Protocole de prise en charge de l'hypertension — CHU",
        url="https://www.chu-casablanca.ma/",
        excerpt="Exemple de source simulée : seuils diagnostiques et suivi recommandé pour l'hypertension artérielle.",
    ),
]

_DISCLAIMER = (
    "⚠️ **Réponse simulée (MockRAGService).** Le moteur RAG réel de la Personne 2 "
    "n'est pas encore branché. Cette réponse et ces sources sont fictives, générées "
    "uniquement pour démontrer l'expérience de chat de bout en bout."
)


class MockRAGService(RAGService):
    """Fake-but-realistic RAG engine used until `RealRAGService` is ready."""

    def __init__(self, seed: int | None = 42) -> None:
        self._rng = random.Random(seed)
        logger.info("MockRAGService initialized — no RAG libraries loaded.")

    def is_ready(self) -> bool:
        return False  # Always False: this is never the "production-grade" engine.

    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        question = question.strip()
        logger.info("MockRAGService answering (fake): %r", question)

        sample_sources = self._rng.sample(_MOCK_KNOWLEDGE_BASE, k=min(2, len(_MOCK_KNOWLEDGE_BASE)))

        if language == "ary-arab":
            body = (
                f"سمعتك سولتي: *\"{question}\"*.\n\n"
                "هادي جواب ديال تجربة (mock) — راه المحرك الحقيقي مازال ما تصاوبش."
            )
        elif language in {"ary", "ary-latn"}:
            body = (
                f"Sme3tek swelti: *\"{question}\"*.\n\n"
                "Hada jawab dyal tajriba (mock) — lmo7arrik l7a9i9i mazal ma khddamch."
            )
        else:
            body = (
                f"Vous avez demandé : *\"{question}\"*.\n\n"
                "Voici une réponse de démonstration générée à partir de sources "
                "simulées, en attendant l'implémentation du moteur RAG réel par "
                "la Personne 2."
            )

        return RAGAnswer(
            answer=f"{_DISCLAIMER}\n\n{body}",
            sources=sample_sources,
            is_mock=True,
        )
