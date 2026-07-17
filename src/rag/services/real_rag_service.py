"""
RealRAGService — PERSON 2's implementation.

Wires SentenceTransformerEmbedder + ChromaVectorStore + SimpleRetriever +
MedicalPromptBuilder + OpenAILLMClient behind the `RAGService` interface.
Heavy imports stay lazy inside `__init__` (see module docstring history):
this file only pulls in sentence-transformers/chromadb/openai the moment
`RAG_MODE=real` actually instantiates it.
"""

from src.core.config import settings
from src.core.exceptions import RetrievalError
from src.core.logging_config import get_logger
from src.rag.interfaces.rag_service_interface import (
    RAGAnswer,
    RAGService,
    SourceCitation,
)

logger = get_logger(__name__)


class RealRAGService(RAGService):
    """Production RAG engine — SentenceTransformer embeddings, ChromaDB, OpenAI."""

    def __init__(self) -> None:
        from src.rag.embedders.sentence_transformer_embedder import (
            SentenceTransformerEmbedder,
        )
        from src.rag.llm.openai_client import OpenAILLMClient
        from src.rag.prompting.medical_prompt_builder import MedicalPromptBuilder
        from src.rag.retrievers.simple_retriever import SimpleRetriever
        from src.rag.vector_stores.chroma_store import ChromaVectorStore

        self.embedder = SentenceTransformerEmbedder(settings.embedding_model_name)
        self.vector_store = ChromaVectorStore(settings.vector_store_path)
        self.retriever = SimpleRetriever(self.embedder, self.vector_store)
        self.prompt_builder = MedicalPromptBuilder()
        self.llm = OpenAILLMClient(settings.llm_model_name, settings.llm_api_key)

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

        chunks = self.retriever.retrieve(question, top_k=settings.top_k)
        prompt = self.prompt_builder.build(question, chunks, language)
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
