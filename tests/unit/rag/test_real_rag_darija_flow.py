"""Darija retrieval-flow tests using doubles only (no ML models or network)."""

from src.preprocessing.interfaces.document_loader_interface import DocumentChunk
from src.rag.interfaces.llm_interface import LLMResponse
from src.rag.interfaces.vector_store_interface import RetrievedChunk
from src.rag.services.real_rag_service import RealRAGService
from src.rag.translation.darija_translator import TranslationResult


class _Translator:
    def to_french(self, text: str) -> TranslationResult:
        return TranslationResult(text, "Est-ce que le diabète est contagieux ?")


class _Retriever:
    def __init__(self) -> None:
        self.query = ""

    def retrieve(self, query: str, top_k: int):
        self.query = query
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    chunk_id="c1",
                    text="Le diabète n'est pas une maladie contagieuse.",
                    source_id="s1",
                    source_title="Guide médical",
                    source_url="https://example.ma/guide",
                ),
                score=0.9,
            )
        ]


class _PromptBuilder:
    SYSTEM_PROMPT = "medical system prompt"

    def __init__(self) -> None:
        self.arguments = None

    def build(self, question, chunks, language, retrieval_question=None):
        self.arguments = (question, language, retrieval_question)
        return "final prompt"


class _LLM:
    def generate(self, prompt, system_prompt=None):
        return LLMResponse("لا، السكري ما كيعداش [1].", "fake")


def test_darija_is_translated_only_for_retrieval(monkeypatch):
    monkeypatch.setattr(
        "src.rag.services.real_rag_service.settings.enable_darija_support", True
    )
    service = RealRAGService.__new__(RealRAGService)
    service.translator = _Translator()
    service.retriever = _Retriever()
    service.prompt_builder = _PromptBuilder()
    service.llm = _LLM()

    answer = service.answer_question("واش السكري كيعدي؟", language="ary-arab")

    assert service.retriever.query == "Est-ce que le diabète est contagieux ?"
    assert service.prompt_builder.arguments == (
        "واش السكري كيعدي؟",
        "ary-arab",
        "Est-ce que le diabète est contagieux ?",
    )
    assert answer.answer == "لا، السكري ما كيعداش [1]."
    assert answer.sources[0].title == "Guide médical"
