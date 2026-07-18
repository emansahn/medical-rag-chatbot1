"""Unit test for OpenAILLMClient's fail-fast config check — no network call."""

import pytest

from src.core.exceptions import LLMGenerationError
from src.rag.llm.openai_client import OpenAILLMClient


def test_missing_api_key_raises_clear_error():
    with pytest.raises(LLMGenerationError):
        OpenAILLMClient(model_name="gpt-4o-mini", api_key="")
