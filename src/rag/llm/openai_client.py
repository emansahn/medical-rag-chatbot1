"""
OpenAILLMClient — Indexation & Moteur RAG's `LLMClient` implementation.

`openai` is imported lazily inside `__init__`, matching the rest of this
module: the file can exist in the repo without forcing the dependency on
modules that do not instantiate the production RAG service.
"""

from typing import Optional

from src.core.exceptions import LLMGenerationError
from src.core.logging_config import get_logger
from src.rag.interfaces.llm_interface import LLMClient, LLMResponse

logger = get_logger(__name__)


class OpenAILLMClient(LLMClient):
    """Generates answers via the OpenAI chat completions API."""

    def __init__(self, model_name: str, api_key: str) -> None:
        if not api_key:
            raise LLMGenerationError(
                "LLM_API_KEY is not configured. Set it in .env (with LLM_PROVIDER=openai) "
                "before using the OpenAI production provider."
            )
        from openai import OpenAI

        self.model_name = model_name
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model_name, messages=messages
            )
        except Exception as exc:
            logger.exception("OpenAI generation failed")
            raise LLMGenerationError(f"LLM generation failed: {exc}") from exc

        choice = response.choices[0]
        return LLMResponse(
            answer=choice.message.content or "",
            model_name=self.model_name,
            finish_reason=choice.finish_reason or "stop",
        )
