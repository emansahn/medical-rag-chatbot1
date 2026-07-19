"""
OllamaLLMClient — Indexation & Moteur RAG's `LLMClient` implementation for a local LLM.

Talks to a local Ollama server (https://ollama.com) — no API key, no
external network call once the model is pulled (`ollama pull llama3.2`).
`ollama` is imported lazily inside `__init__`, matching the rest of this
module: the file can exist in the repo without forcing the dependency on
modules that do not instantiate the production RAG service.
"""

from typing import Optional

from src.core.exceptions import LLMGenerationError
from src.core.logging_config import get_logger
from src.rag.interfaces.llm_interface import LLMClient, LLMResponse

logger = get_logger(__name__)


class OllamaLLMClient(LLMClient):
    """Generates answers via a local Ollama server (chat endpoint)."""

    def __init__(
        self,
        model_name: str,
        base_url: str,
        num_predict: int = 256,
        temperature: float = 0.1,
        keep_alive: str = "30m",
    ) -> None:
        from ollama import Client

        self.model_name = model_name
        self._client = Client(host=base_url)
        self._options = {
            "num_predict": num_predict,
            "temperature": temperature,
        }
        self._keep_alive = keep_alive

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat(
                model=self.model_name,
                messages=messages,
                options=self._options,
                keep_alive=self._keep_alive,
            )
        except Exception as exc:
            logger.exception("Ollama generation failed")
            raise LLMGenerationError(
                f"Ollama generation failed (model={self.model_name!r}): {exc}. "
                "Is the Ollama server running (`ollama serve`) and the model pulled "
                f"(`ollama pull {self.model_name}`)?"
            ) from exc

        return LLMResponse(
            answer=response.message.content or "",
            model_name=self.model_name,
            finish_reason=response.done_reason or "stop",
        )
