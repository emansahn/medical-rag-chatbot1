"""Darija-to-French query translation used before vector retrieval."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from src.core.exceptions import LLMGenerationError
from src.rag.interfaces.llm_interface import LLMClient
from src.rag.translation.medical_glossary import find_relevant_terms


@dataclass(frozen=True)
class TranslationResult:
    original_text: str
    translated_text: str
    source_language: str = "ary"
    target_language: str = "fr"


class DarijaTranslator(ABC):
    """Contract for translating a retrieval query without answering it."""

    @abstractmethod
    def to_french(self, text: str) -> TranslationResult:
        raise NotImplementedError


class LLMDarijaTranslator(DarijaTranslator):
    """Translate Moroccan Darija with the already configured application LLM."""

    SYSTEM_PROMPT = (
        "Tu es un traducteur spécialisé en darija marocaine médicale. "
        "Traduis fidèlement la question en français pour une recherche documentaire. "
        "N'y réponds jamais, n'ajoute aucune explication, aucun diagnostic et aucune "
        "information absente. Conserve les négations, symptômes, durées, doses et noms "
        "de médicaments. Retourne uniquement la traduction française, sur une seule ligne."
    )

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def to_french(self, text: str) -> TranslationResult:
        original = text.strip()
        if not original:
            raise LLMGenerationError("Cannot translate an empty Darija question.")

        glossary_lines = [
            f"- {entry.arabic} / {entry.latin} = {french}"
            for french, entry in find_relevant_terms(original).items()
        ]
        glossary = "\n".join(glossary_lines) or "(aucun terme contrôlé détecté)"
        prompt = (
            "GLOSSAIRE À RESPECTER SI PERTINENT:\n"
            f"{glossary}\n\n"
            "QUESTION EN DARIJA:\n"
            f"{original}\n\n"
            "TRADUCTION FRANÇAISE UNIQUEMENT:"
        )
        response = self._llm.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
        translated = self._clean_translation(response.answer)
        if not translated:
            raise LLMGenerationError("The Darija translator returned an empty translation.")

        return TranslationResult(original_text=original, translated_text=translated)

    @staticmethod
    def _clean_translation(text: str) -> str:
        cleaned = text.strip().strip("`").strip()
        cleaned = re.sub(
            r"^(?:traduction(?:\s+française)?|français)\s*:\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return " ".join(cleaned.split())
