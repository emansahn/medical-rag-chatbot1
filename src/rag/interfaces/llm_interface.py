"""
Interface: LLM generation & prompt construction — Indexation & Moteur RAG's contract.

Abstracts away the specific LLM backend (OpenAI API, Ollama local model,
HuggingFace...) so `RealRAGService`
(`src/rag/services/real_rag_service.py`, the Indexation & Moteur RAG integration point) can call `generate()` without caring
which provider is behind it.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from src.rag.interfaces.vector_store_interface import RetrievedChunk


@dataclass
class LLMResponse:
    """Structured output of a generation call."""

    answer: str
    model_name: str
    finish_reason: str = "stop"


class PromptBuilder(ABC):
    """Abstract base class for turning (question, retrieved chunks) into a
    final prompt string sent to the LLM.

    Must enforce the project's core anti-hallucination rule: the LLM should
    answer *only* from the provided context, and say so explicitly when the
    context does not contain the answer.
    """

    @abstractmethod
    def build(
        self,
        question: str,
        context_chunks: List[RetrievedChunk],
        language: str = "fr",
        retrieval_question: Optional[str] = None,
    ) -> str:
        raise NotImplementedError


class LLMClient(ABC):
    """Abstract base class for the generation backend."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response for the given prompt."""
        raise NotImplementedError
