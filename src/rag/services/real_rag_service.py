"""
RealRAGService — Indexation & Moteur RAG's production engine implementation.

Wires SentenceTransformerEmbedder + ChromaVectorStore + SimpleRetriever +
MedicalPromptBuilder + an `LLMClient` behind the `RAGService` interface.
The LLM backend is picked from `LLM_PROVIDER` ("ollama", local and
dependency-free of any API key, or "openai") — adding a new backend later
means one new `LLMClient` implementation plus one branch in
`_build_llm_client`, nothing else in this file changes (Open/Closed).
Heavy imports stay lazy inside `__init__`: this file only pulls in
sentence-transformers/chromadb/ollama the moment `RAG_MODE=real` actually
instantiates it.
"""

from src.core.config import settings
from src.core.exceptions import LLMGenerationError, RetrievalError
from src.core.logging_config import get_logger
from src.rag.interfaces.llm_interface import LLMClient
from src.rag.interfaces.rag_service_interface import (
    RAGAnswer,
    RAGService,
    SourceCitation,
)

logger = get_logger(__name__)


def _build_llm_client() -> LLMClient:
    if settings.llm_provider == "ollama":
        from src.rag.llm.ollama_client import OllamaLLMClient

        return OllamaLLMClient(settings.llm_model_name, settings.llm_base_url)
    if settings.llm_provider == "openai":
        from src.rag.llm.openai_client import OpenAILLMClient

        return OpenAILLMClient(settings.llm_model_name, settings.llm_api_key)
    raise LLMGenerationError(
        f"Unsupported LLM_PROVIDER={settings.llm_provider!r}. Use 'ollama' (local) or 'openai'."
    )


class RealRAGService(RAGService):
    """Production RAG engine — SentenceTransformer embeddings, ChromaDB, local/OpenAI LLM."""

    def __init__(self) -> None:
        from src.rag.embedders.sentence_transformer_embedder import (
            SentenceTransformerEmbedder,
        )
        from src.rag.prompting.medical_prompt_builder import MedicalPromptBuilder
        from src.rag.retrievers.simple_retriever import SimpleRetriever
        from src.rag.vector_stores.chroma_store import ChromaVectorStore
        from src.rag.translation.darija_translator import LLMDarijaTranslator

        self.embedder = SentenceTransformerEmbedder(settings.embedding_model_name)
        self.vector_store = ChromaVectorStore(settings.vector_store_path)
        self.retriever = SimpleRetriever(self.embedder, self.vector_store)
        self.prompt_builder = MedicalPromptBuilder()
        self.llm = _build_llm_client()
        self.translator = LLMDarijaTranslator(self.llm)

        if not self.vector_store.is_ready():
            logger.warning(
                "Vector store at %s is empty — run `python -m src.rag.ingest` before "
                "expecting grounded answers.",
                settings.vector_store_path,
            )
        logger.info(
            "RealRAGService initialized (embedding_model=%s, llm_model=%s).",
            settings.embedding_model_name,
            settings.llm_model_name,
        )

    def is_ready(self) -> bool:
        return self.vector_store.is_ready()

    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        question = question.strip()
        if not question:
            raise RetrievalError("Cannot answer an empty question.")

        retrieval_question = question
        if settings.enable_darija_support and language in {"ary", "ary-arab", "ary-latn"}:
            try:
                translation = self.translator.to_french(question)
                retrieval_question = translation.translated_text
                logger.info("Darija query translated to French for retrieval.")
            except LLMGenerationError as exc:
                logger.warning(
                    "Darija translation failed; falling back to multilingual retrieval: %s",
                    exc,
                )

        chunks = self.retriever.retrieve(retrieval_question, top_k=settings.top_k)
        prompt = self.prompt_builder.build(
            question,
            chunks,
            language,
            retrieval_question=retrieval_question,
        )
        response = self.llm.generate(
            prompt, system_prompt=self.prompt_builder.SYSTEM_PROMPT
        )

        sources = [
            SourceCitation(
                title=item.chunk.source_title,
                url=item.chunk.source_url,
                excerpt=item.chunk.text[:300],
            )
            for item in chunks
        ]
        return RAGAnswer(answer=response.answer, sources=sources, is_mock=False)
