"""
TextCleaner for French-language Moroccan medical PDFs and OMS web pages.

Rules below come from real noise observed in data/raw/ (isolated page-number
lines, PDF form-feed artifacts) and in scraped OMS pages (search-widget
boilerplate) — see the exploratory scripts run against those sources.

Does NOT attempt to repair structural issues like flattened PDF tables (e.g.
comma-separated lists bled onto a single line) — that is a known layout
limitation of the loaders, not noise for this cleaner to strip.
"""
import re
from typing import Iterable, List, Optional

from src.preprocessing.interfaces.document_loader_interface import TextCleaner

# Empirique : observée sur les sites scrapés pendant le développement
# (notamment emro.who.int), pas garantie de couvrir tout nouveau site ajouté
# plus tard. Limitation connue à documenter dans le rapport final si de
# nouvelles sources web sont ajoutées après cette date.
DEFAULT_WEB_NOISE_PHRASES: List[str] = [
    "Recherche",
    "Filtrer par date",
    "Wildcard",
    "Requête floue",
    "Plan du site",
    "Menu principal",
    "Ouvrir le calendrier",
    "Rechercher:",
    "Tous les mots",
    "N'importe quel mot",
    "Phrase exacte",
    "Préfixe de phrase",
    "Sélectionnez votre langue",
]

_PAGE_NUMBER_LINE_PATTERN = re.compile(
    r"""^(?:
        \d+                # "12"
        | -\s*\d+\s*-      # "- 12 -"
        | page\s+\d+       # "Page 12"
        | \d+\s*/\s*\d+    # "12 / 340"
    )$""",
    re.VERBOSE | re.IGNORECASE,
)

_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class FrenchMedicalCleaner(TextCleaner):
    """Deterministic cleaner: strips page-number lines, control characters,
    excess whitespace, and known web-navigation noise. Pure function — same
    input always yields the same output, no file or network access.

    Args:
        web_noise_phrases: Lines containing any of these substrings are
            dropped (step 4). Defaults to `DEFAULT_WEB_NOISE_PHRASES`; pass
            your own list (or extend the default) to add more patterns as
            new noisy sources are found.
    """

    def __init__(self, web_noise_phrases: Optional[Iterable[str]] = None) -> None:
        self.web_noise_phrases = list(web_noise_phrases) if web_noise_phrases is not None else list(DEFAULT_WEB_NOISE_PHRASES)

    def clean(self, raw_text: str) -> str:
        text = self._strip_page_number_lines(raw_text)
        text = self._strip_control_characters(text)
        text = self._normalize_whitespace(text)
        text = self._strip_web_noise_lines(text)
        return text

    def _strip_page_number_lines(self, text: str) -> str:
        lines = [line for line in text.split("\n") if not _PAGE_NUMBER_LINE_PATTERN.match(line.strip())]
        return "\n".join(lines)

    def _strip_control_characters(self, text: str) -> str:
        return _CONTROL_CHARS_PATTERN.sub("", text)

    def _normalize_whitespace(self, text: str) -> str:
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))

    def _strip_web_noise_lines(self, text: str) -> str:
        if not self.web_noise_phrases:
            return text
        lines = [line for line in text.split("\n") if not any(phrase in line for phrase in self.web_noise_phrases)]
        return "\n".join(lines)
