"""
MedicalPromptBuilder — Indexation & Moteur RAG's `PromptBuilder` implementation.

Enforces the project's core anti-hallucination rule directly in the
returned prompt string (not only via a separate system prompt), so the
constraint holds even if a caller forgets to pass `system_prompt` to
`LLMClient.generate()`. `SYSTEM_PROMPT` is still exposed separately so
`RealRAGService` can pass it to providers (like OpenAI) that give the
system role special weight.
"""

from typing import List, Optional

from src.rag.interfaces.llm_interface import PromptBuilder
from src.rag.interfaces.vector_store_interface import RetrievedChunk
from src.rag.translation.medical_glossary import find_relevant_terms

_LANGUAGE_NAMES = {
    "fr": "français",
    "ary": "darija marocaine (transcrite en alphabet latin)",
    "ary-arab": "darija marocaine en alphabet arabe",
    "ary-latn": "darija marocaine en alphabet latin",
}

_DARIJA_INSTRUCTIONS = {
    "ary": (
        "Réponds en darija marocaine simple, transcrite uniquement en alphabet latin. "
        "Explique les termes médicaux difficiles et conserve les citations [1], [2]."
    ),
    "ary-arab": (
        "جاوب بالدارجة المغربية البسيطة وبالحروف العربية. شرح الكلمات الطبية الصعبة. "
        "ما تديرش تشخيص وما تعطيش علاج شخصي. حافظ على المراجع [1] و[2]."
    ),
    "ary-latn": (
        "Jawb b-darija lmaghribiya basita, ghir b-l7orof latiniya. "
        "Chra7 lkalimat tibbia s3ab. Matdirch diagnostic w mat3tich traitement "
        "personnalise. Khalli les citations [1] w [2] kif ma homa."
    ),
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
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
        language: str = "fr",
        retrieval_question: Optional[str] = None,
    ) -> str:
        language_name = _LANGUAGE_NAMES.get(language, "français")
        language_instruction = _DARIJA_INSTRUCTIONS.get(language, "")
        glossary = self._format_relevant_glossary(question, language)
        translated_question = (
            f"\nQUESTION TRADUITE POUR LA RECHERCHE:\n{retrieval_question.strip()}\n"
            if retrieval_question and retrieval_question.strip() != question.strip()
            else ""
        )

        if not context_chunks:
            return (
                f"{self.SYSTEM_PROMPT}\n\n"
                "CONTEXTE: (aucun passage pertinent trouvé dans la base documentaire)\n\n"
                f"QUESTION:\n{question.strip()}\n\n"
                f"{translated_question}"
                f"{language_instruction}\n{glossary}\n"
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
            f"{translated_question}"
            f"INSTRUCTIONS DE LANGUE:\n{language_instruction or 'Réponds en français clair.'}\n\n"
            f"GLOSSAIRE TERMINOLOGIQUE:\n{glossary}\n\n"
            f"Réponds en {language_name}, en citant tes sources avec [1], [2], etc."
        )

    @staticmethod
    def _format_relevant_glossary(question: str, language: str) -> str:
        """Include only terminology found in the question, never medical facts."""

        if language not in _DARIJA_INSTRUCTIONS:
            return "(non requis)"

        matches = find_relevant_terms(question)
        if not matches:
            return "(aucun terme contrôlé détecté)"

        use_arabic = language == "ary-arab"
        return "\n".join(
            f"- {french} = {entry.arabic if use_arabic else entry.latin}"
            for french, entry in matches.items()
        )
