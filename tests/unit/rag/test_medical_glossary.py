"""Tests for the controlled French/Darija medical glossary."""

from src.rag.translation.medical_glossary import (
    MEDICAL_GLOSSARY,
    find_relevant_terms,
)


def test_initial_glossary_has_required_fields():
    assert len(MEDICAL_GLOSSARY) >= 20
    assert all(entry.arabic and entry.latin for entry in MEDICAL_GLOSSARY.values())


def test_finds_french_term_without_accents():
    matches = find_relevant_terms("Quels sont les symptômes du diabete ?")

    assert "diabète" in matches
    assert matches["diabète"].arabic == "داء السكري"


def test_finds_latin_darija_alias():
    matches = find_relevant_terms("3ndi wja3 f sder w di9 nafas")

    assert "douleur thoracique" in matches
    assert "difficulté à respirer" in matches


def test_finds_arabic_darija_alias():
    matches = find_relevant_terms("عندي السخانة والكحة")

    assert "fièvre" in matches
    assert "toux" in matches


def test_short_alias_does_not_match_inside_unrelated_word():
    matches = find_relevant_terms("La tension narrative de ce texte est forte")

    assert "pression artérielle" not in matches
