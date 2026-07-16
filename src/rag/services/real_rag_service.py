"""
RealRAGService — PERSON 2 implements this class.

Deliberately empty/placeholder today. Heavy imports (sentence-transformers,
chromadb, faiss, langchain) are done LAZILY inside `__init__`, not at module
level — this means simply having this *file* in the repo never forces those
libraries to be installed; they're only required the moment someone actually
instantiates `RealRAGService` (which only happens when `RAG_MODE=real`, see
`src/rag/container.py`).

Person 2's task: implement `Embedder`, `VectorStore`/`Retriever`,
`PromptBuilder`, `LLMClient` from `src/rag/interfaces/`, then fill in the
methods below. Once `is_ready()` can return True, flip `RAG_MODE=real` in
`.env` — nothing in the backend or frontend needs to change.
"""
from src.core.logging_config import get_logger
from src.rag.interfaces.rag_service_interface import RAGAnswer, RAGService

logger = get_logger(__name__)


class RealRAGService(RAGService):
    """Production RAG engine — TODO(Person 2): implement this class."""

    def __init__(self) -> None:
        # TODO(Person 2): lazily import and construct your real components here, e.g.:
        #
        #   from src.rag.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
        #   from src.rag.vector_stores.chroma_store import ChromaVectorStore
        #   from src.rag.retrievers.simple_retriever import SimpleRetriever
        #   from src.rag.prompting.medical_prompt_builder import MedicalPromptBuilder
        #   from src.rag.llm.openai_client import OpenAILLMClient
        #   from src.core.config import settings
        #
        #   self.embedder = SentenceTransformerEmbedder(settings.embedding_model_name)
        #   self.vector_store = ChromaVectorStore(settings.vector_store_path)
        #   self.retriever = SimpleRetriever(self.embedder, self.vector_store)
        #   self.prompt_builder = MedicalPromptBuilder()
        #   self.llm = OpenAILLMClient(settings.llm_model_name, settings.llm_api_key)
        #
        # Keeping these imports here (not at module top) is what lets the rest
        # of the app boot without person2-rag.txt installed, even when this
        # class exists in the codebase.
        raise NotImplementedError(
            "RealRAGService is not implemented yet. Person 2: fill in __init__ and "
            "answer_question() using src/rag/interfaces/*, then set RAG_MODE=real in .env."
        )

    def is_ready(self) -> bool:
        # TODO(Person 2): return True once the vector store is populated and the
        # LLM client is configured, e.g. `return self.vector_store.is_ready()`.
        return False

    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        # TODO(Person 2): implement the real retrieve -> prompt -> generate flow, e.g.:
        #
        #   chunks = self.retriever.retrieve(question, top_k=settings.top_k)
        #   prompt = self.prompt_builder.build(question, chunks, language)
        #   response = self.llm.generate(prompt)
        #   sources = [SourceCitation(c.chunk.source_title, c.chunk.source_url, c.chunk.text[:200])
        #              for c in chunks]
        #   return RAGAnswer(answer=response.answer, sources=sources, is_mock=False)
        raise NotImplementedError
