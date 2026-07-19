"""Small, reviewed French/Darija medical terminology glossary.

This glossary is a linguistic aid for translation and prompt construction. It
must never be treated as a medical knowledge source: facts and recommendations
must continue to come from documents retrieved by the RAG pipeline.

The initial entries cover common primary-care and emergency vocabulary. New
terms should be reviewed by both a Moroccan Darija speaker and someone with
medical knowledge before being merged.
"""

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class MedicalGlossaryEntry:
    """Approved Darija equivalents and common ways users may write a term."""

    arabic: str
    latin: str
    aliases: tuple[str, ...] = ()


MEDICAL_GLOSSARY: dict[str, MedicalGlossaryEntry] = {
    "allergie": MedicalGlossaryEntry("الحساسية", "l7assasiya", ("7assasiya", "حساسية")),
    "antibiotique": MedicalGlossaryEntry("مضاد حيوي", "modad 7ayawi", ("antibiotic", "مضاد حيوي")),
    "asthme": MedicalGlossaryEntry("الربو", "rbo", ("rebou", "الربو")),
    "AVC": MedicalGlossaryEntry("السكتة الدماغية", "sakta dimaghiya", ("جلطة دماغية", "attaque cérébrale")),
    "cancer": MedicalGlossaryEntry("السرطان", "saratan", ("سرطان",)),
    "cholestérol": MedicalGlossaryEntry("الكوليسترول", "kolesterol", ("cholesterol", "كوليسترول")),
    "diabète": MedicalGlossaryEntry("داء السكري", "sokkari", ("diabete", "sokkar", "سكري", "السكري")),
    "diarrhée": MedicalGlossaryEntry("الإسهال", "ishal", ("diarrhee", "إسهال")),
    "difficulté à respirer": MedicalGlossaryEntry("ضيق فالتنفس", "di9 f tnaffos", ("ضيق التنفس", "di9 nafas", "essoufflement")),
    "douleur": MedicalGlossaryEntry("الوجع", "lwja3", ("wja3", "ألم", "وجع")),
    "douleur thoracique": MedicalGlossaryEntry("وجع فالصدر", "wja3 f sder", ("mal à la poitrine", "mal f sder", "ألم في الصدر", "وجع الصدر")),
    "fièvre": MedicalGlossaryEntry("السخانة", "skhana", ("fievre", "7rara", "température", "حمى", "سخانة")),
    "grossesse": MedicalGlossaryEntry("الحمل", "l7aml", ("enceinte", "7amla", "حامل", "حاملة")),
    "hypertension artérielle": MedicalGlossaryEntry("ارتفاع ضغط الدم", "daght ddem tale3", ("hypertension", "tension haute", "daght", "الضغط", "ضغط الدم")),
    "infection": MedicalGlossaryEntry("التعفن", "ta3affon", ("تعفن", "عدوى", "infection bactérienne")),
    "médicament": MedicalGlossaryEntry("الدواء", "dwa", ("medicament", "dawa", "دواء", "الدوا")),
    "nausée": MedicalGlossaryEntry("الغثيان", "lghathayan", ("nausée", "الغثيان", "t9iya")),
    "ordonnance": MedicalGlossaryEntry("الوصفة الطبية", "wasfa tibbiya", ("prescription", "وصفة طبية")),
    "pression artérielle": MedicalGlossaryEntry("ضغط الدم", "daght ddem", ("tension artérielle", "ضغط الدم")),
    "rhume": MedicalGlossaryEntry("الزكام", "zkom", ("zokam", "زكام")),
    "toux": MedicalGlossaryEntry("الكحة", "ko7a", ("toux sèche", "ke7a", "كحة", "السعال")),
    "tuberculose": MedicalGlossaryEntry("السل", "ssel", ("TB", "الدرن", "سل")),
    "tuberculine": MedicalGlossaryEntry("التوبركولين", "tuberkulin", ("IDR", "اختبار التوبركولين")),
    "revaccination": MedicalGlossaryEntry("إعادة التلقيح", "i3adat tal9i7", ("rappel vaccinal",)),
    "urgence médicale": MedicalGlossaryEntry("حالة طبية مستعجلة", "7ala tibbiya mosta3jila", ("urgence", "mosta3jalat", "المستعجلات", "حالة مستعجلة")),
    "vaccin": MedicalGlossaryEntry("اللقاح", "li9a7", ("vaccination", "tal9i7", "تلقيح", "لقاح")),
    "vertige": MedicalGlossaryEntry("الدوخة", "dokha", ("doukha", "دوخة", "tête qui tourne")),
    "vomissement": MedicalGlossaryEntry("التقيؤ", "t9iya", ("vomir", "قيء", "تقيؤ")),
}


def _normalize(text: str) -> str:
    """Normalize Latin accents/case and whitespace while preserving Arabic."""

    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_marks).strip()


def find_relevant_terms(text: str) -> dict[str, MedicalGlossaryEntry]:
    """Return glossary entries whose French term or alias occurs in ``text``.

    Matching is deliberately deterministic and dependency-free. Latin words
    use token boundaries so short aliases are not found inside unrelated
    words; Arabic and multi-word expressions use normalized substring search.
    """

    normalized_text = _normalize(text)
    matches: dict[str, MedicalGlossaryEntry] = {}

    for french_term, entry in _approved_glossary().items():
        candidates = (french_term, entry.arabic, entry.latin, *entry.aliases)
        for candidate in candidates:
            normalized_candidate = _normalize(candidate)
            if not normalized_candidate:
                continue
            if re.search(r"[a-z0-9]", normalized_candidate):
                pattern = rf"(?<![a-z0-9]){re.escape(normalized_candidate)}(?![a-z0-9])"
                found = re.search(pattern, normalized_text) is not None
            else:
                found = normalized_candidate in normalized_text
            if found:
                matches[french_term] = entry
                break

    return matches


def _approved_glossary() -> dict[str, MedicalGlossaryEntry]:
    """Load the live approved glossary from SQLite, with safe startup fallback."""

    try:
        # Local import prevents a module cycle while SQLite seeds its first rows
        # from MEDICAL_GLOSSARY during application startup.
        from src.admin.database import get_admin_database

        return {
            row["french"]: MedicalGlossaryEntry(
                arabic=row["arabic"],
                latin=row["latin"],
                aliases=tuple(row["aliases"]),
            )
            for row in get_admin_database().approved_terms()
        }
    except (OSError, RuntimeError):
        return MEDICAL_GLOSSARY
