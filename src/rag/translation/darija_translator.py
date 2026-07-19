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

        controlled_terms = find_relevant_terms(original)
        missing_terms = [
            term
            for term in controlled_terms
            if term.casefold() not in translated.casefold()
        ]
        acronyms = re.findall(r"\b[A-Z][A-Z0-9-]{1,}\b", original)
        retrieval_terms = [*missing_terms, *acronyms]
        if retrieval_terms:
            translated = f"{translated} {' '.join(dict.fromkeys(retrieval_terms))}"
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


class LLMDarijaResponseTranslator:
    """Translate an already grounded French answer without changing its facts."""

    _PROMPTS = {
        "ary": "darija marocaine naturelle en alphabet latin",
        "ary-latn": "darija marocaine naturelle en alphabet latin",
        "ary-arab": "darija marocaine naturelle en alphabet arabe",
    }

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def from_french(self, text: str, language: str) -> str:
        target = self._PROMPTS.get(language)
        if not target:
            raise LLMGenerationError(f"Unsupported Darija output language: {language}")
        system_prompt = (
            f"Tu traduis du français vers la {target}. "
            "Traduis fidèlement sans ajouter, supprimer ou modifier aucune information médicale. "
            "Conserve exactement toutes les citations comme [1], [2] et tous les nombres. "
            "N'ajoute ni titre de source, ni URL, ni commentaire. "
            "N'utilise aucune autre langue, notamment ni français ni chinois. "
            "Terminologie: vaccination=التلقيح/talqih; vaccin=اللقاح/lliqa7; "
            "tuberculose=السل/ssel; nouveau-né=مولود جديد/mouloud jdid; "
            "dose unique=جرعة وحدة/jor3a wa7da; contre-indication=مانع طبي/mane3 tibbi. "
            "tuberculine=التوبركولين/tuberkulin; revaccination=إعادة التلقيح/i3adat tal9i7; "
            "Programme National d'Immunisation=البرنامج الوطني للتلقيح/program watani dyal tal9i7. "
            "Utilise un style marocain simple et quatre phrases courtes au maximum. "
            "Retourne uniquement la traduction."
        )
        response = self._llm.generate(text.strip(), system_prompt=system_prompt)
        translated = response.answer.strip()
        if not translated:
            raise LLMGenerationError("The Darija response translator returned an empty answer.")
        source_citations = list(
            dict.fromkeys(re.findall(r"\[\d+(?:-\d+)?\]", text))
        )
        missing_citations = [
            citation for citation in source_citations if citation not in translated
        ]
        if missing_citations:
            translated = f"{translated} {' '.join(missing_citations)}"
        return translated
