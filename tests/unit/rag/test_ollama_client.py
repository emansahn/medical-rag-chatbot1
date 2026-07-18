"""Unit tests for OllamaLLMClient — the local, API-key-free LLM backend.
`ollama.Client` is mocked, so no local Ollama server needs to be running."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import LLMGenerationError
from src.rag.llm.ollama_client import OllamaLLMClient


def _fake_chat_response(content: str, done_reason: str = "stop"):
    response = MagicMock()
    response.message.content = content
    response.done_reason = done_reason
    return response


def test_generate_returns_answer_from_local_model():
    with patch("ollama.Client") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.chat.return_value = _fake_chat_response("Réponse locale.")

        client = OllamaLLMClient(model_name="llama3.2", base_url="http://localhost:11434")
        response = client.generate("Question ?", system_prompt="system")

        assert response.answer == "Réponse locale."
        assert response.model_name == "llama3.2"
        assert response.finish_reason == "stop"
        instance.chat.assert_called_once_with(
            model="llama3.2",
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "Question ?"},
            ],
        )


def test_generate_without_system_prompt_only_sends_user_message():
    with patch("ollama.Client") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.chat.return_value = _fake_chat_response("ok")

        client = OllamaLLMClient(model_name="llama3.2", base_url="http://localhost:11434")
        client.generate("Question ?")

        instance.chat.assert_called_once_with(
            model="llama3.2", messages=[{"role": "user", "content": "Question ?"}]
        )


def test_generate_wraps_connection_errors():
    with patch("ollama.Client") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.chat.side_effect = ConnectionError("connection refused")

        client = OllamaLLMClient(model_name="llama3.2", base_url="http://localhost:11434")

        with pytest.raises(LLMGenerationError):
            client.generate("Question ?")
