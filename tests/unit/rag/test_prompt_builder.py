"""Unit tests for MedicalPromptBuilder — no server, no network, no ML libraries."""

from src.preprocessing.interfaces.document_loader_interface import DocumentChunk
from src.rag.interfaces.vector_store_interface import RetrievedChunk
from src.rag.prompting.medical_prompt_builder import MedicalPromptBuilder


def _chunk(chunk_id: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=DocumentChunk(
            chunk_id=chunk_id,
            text=text,
            source_id="src-1",
            source_title="Guide de vaccination",
            source_url="https://www.sante.gov.ma/guide",
        ),
        score=0.9,
    )


def test_build_with_context_cites_sources_and_includes_question():
    builder = MedicalPromptBuilder()
    prompt = builder.build(
        "Quel est le calendrier de vaccination ?",
        [
            _chunk(
                "c1", "La vaccination protège contre plusieurs maladies infectieuses."
            )
        ],
    )

    assert "[1]" in prompt
    assert "Guide de vaccination" in prompt
    assert "Quel est le calendrier de vaccination ?" in prompt
    assert "vaccination protège" in prompt


def test_build_degrades_gracefully_with_zero_chunks():
    builder = MedicalPromptBuilder()
    prompt = builder.build("Question sans réponse dans le corpus", [])

    assert "aucun passage pertinent" in prompt.lower()
    assert (
        "ne disposes pas" in prompt.lower()
        or "pas d'une source suffisante" in prompt.lower()
        or "consulter un professionnel" in prompt.lower()
    )


def test_build_respects_darija_language_flag():
    builder = MedicalPromptBuilder()
    prompt = builder.build(
        "Chno howa calendrier dyal talqih", [_chunk("c1", "texte")], language="ary"
    )

    assert "darija" in prompt.lower()


def test_build_uses_arabic_darija_glossary():
    builder = MedicalPromptBuilder()
    prompt = builder.build(
        "واش السكري كيعدي؟", [_chunk("c1", "Le diabète n'est pas contagieux.")],
        language="ary-arab",
    )

    assert "السكري" in prompt
    assert "داء السكري" in prompt
    assert "بالحروف العربية" in prompt


def test_build_uses_latin_darija_glossary():
    builder = MedicalPromptBuilder()
    prompt = builder.build(
        "3ndi wja3 f sder", [_chunk("c1", "Une douleur thoracique exige une évaluation.")],
        language="ary-latn",
    )

    assert "douleur thoracique = wja3 f sder" in prompt
    assert "ghir b-l7orof latiniya" in prompt
