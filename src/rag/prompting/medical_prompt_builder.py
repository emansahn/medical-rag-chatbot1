"""
MedicalPromptBuilder — Indexation & Moteur RAG's `PromptBuilder` implementation.

Enforces the project's core anti-hallucination rule directly in the
returned prompt string (not only via a separate system prompt), so the
constraint holds even if a caller forgets to pass `system_prompt` to
`LLMClient.generate()`. `SYSTEM_PROMPT` is still exposed separately so
`RealRAGService` can pass it to providers (like OpenAI) that give the
system role special weight.
"""

from typing import List

from src.rag.interfaces.llm_interface import PromptBuilder
from src.rag.interfaces.vector_store_interface import RetrievedChunk

_LANGUAGE_NAMES = {
    "fr": "français",
    "ary": "darija marocaine (transcrite en alphabet latin)",
}


class MedicalPromptBuilder(PromptBuilder):
    """Builds a grounded, citation-enforcing prompt for medical questions."""

    SYSTEM_PROMPT = (
        "Tu es un assistant d'information médicale générale adapté au contexte marocain. "
        "Réponds UNIQUEMENT à partir du CONTEXTE fourni. Si le contexte est insuffisant pour "
        "répondre, dis-le explicitement au lieu d'inventer une réponse. N'établis jamais de "
        "diagnostic et ne prescris jamais de traitement personnalisé. En cas de symptômes "
        "graves ou urgents, recommande de contacter immédiatement les services d'urgence. "
        "Cite chaque affirmation avec la source correspondante sous la forme [1], [2]."
    )

    def build(
        self, question: str, context_chunks: List[RetrievedChunk], language: str = "fr"
    ) -> str:
        language_name = _LANGUAGE_NAMES.get(language, "français")

        if not context_chunks:
            return (
                f"{self.SYSTEM_PROMPT}\n\n"
                "CONTEXTE: (aucun passage pertinent trouvé dans la base documentaire)\n\n"
                f"QUESTION:\n{question.strip()}\n\n"
                f"Réponds en {language_name}. Comme le contexte est vide, indique clairement "
                "que tu ne disposes pas d'une source suffisante pour répondre à cette question "
                "et invite l'utilisateur à consulter un professionnel de santé."
            )

        context = "\n\n".join(
            f"[{i}] Source : {item.chunk.source_title} ({item.chunk.source_url})\n{item.chunk.text}"
            for i, item in enumerate(context_chunks, 1)
        )
        return (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"CONTEXTE:\n{context}\n\n"
            f"QUESTION:\n{question.strip()}\n\n"
            f"Réponds en {language_name}, en citant tes sources avec [1], [2], etc."
        )
