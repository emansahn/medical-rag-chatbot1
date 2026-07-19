"""Unit tests for Darija query translation without network or a real LLM."""

import pytest

from src.core.exceptions import LLMGenerationError
from src.rag.interfaces.llm_interface import LLMClient, LLMResponse
from src.rag.translation.darija_translator import LLMDarijaTranslator


class _FakeLLM(LLMClient):
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompt = ""
        self.system_prompt = None

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        self.prompt = prompt
        self.system_prompt = system_prompt
        return LLMResponse(answer=self.answer, model_name="fake")


def test_translates_darija_and_includes_relevant_glossary():
    llm = _FakeLLM("Traduction française : Est-ce que le diabète est contagieux ?")
    translator = LLMDarijaTranslator(llm)

    result = translator.to_french("واش السكري كيعدي؟")

    assert result.translated_text == "Est-ce que le diabète est contagieux ?"
    assert result.original_text == "واش السكري كيعدي؟"
    assert "diabète" in llm.prompt
    assert "N'y réponds jamais" in llm.system_prompt


def test_cleans_code_fences_and_whitespace():
    translator = LLMDarijaTranslator(_FakeLLM("```  J'ai mal à la poitrine.  ```"))

    result = translator.to_french("3ndi wja3 f sder")

    assert result.translated_text == "J'ai mal à la poitrine."


def test_rejects_empty_input():
    translator = LLMDarijaTranslator(_FakeLLM("ignored"))

    with pytest.raises(LLMGenerationError):
        translator.to_french("   ")


def test_rejects_empty_llm_translation():
    translator = LLMDarijaTranslator(_FakeLLM("   "))

    with pytest.raises(LLMGenerationError):
        translator.to_french("chno howa diabete")
