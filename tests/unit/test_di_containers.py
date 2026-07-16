"""Unit tests for the RAG and data-provider dependency-injection containers."""
from src.preprocessing.container import get_chunk_provider, get_dataset_loader, get_document_provider
from src.preprocessing.interfaces.data_provider_interface import ChunkProvider, DatasetLoader, DocumentProvider
from src.rag.container import get_rag_service
from src.rag.interfaces.rag_service_interface import RAGService
from src.rag.services.mock_rag_service import MockRAGService


def test_default_mode_is_mock_rag_service():
    """With default settings (RAG_MODE=mock), the container must return a
    MockRAGService and never attempt to import FAISS/LangChain/etc."""
    service = get_rag_service()
    assert isinstance(service, RAGService)
    assert isinstance(service, MockRAGService)
    assert service.is_ready() is False


def test_mock_rag_service_answers_without_heavy_dependencies():
    service = MockRAGService()
    answer = service.answer_question("Quels sont les symptômes de la grippe ?")
    assert answer.answer
    assert answer.is_mock is True
    assert len(answer.sources) > 0


def test_default_mode_is_mock_data_providers():
    doc_provider = get_document_provider()
    chunk_provider = get_chunk_provider()
    dataset_loader = get_dataset_loader()

    assert isinstance(doc_provider, DocumentProvider)
    assert isinstance(chunk_provider, ChunkProvider)
    assert isinstance(dataset_loader, DatasetLoader)

    assert doc_provider.count() > 0
    assert chunk_provider.count() > 0

    dataset = dataset_loader.load()
    assert len(dataset.documents) > 0
    assert len(dataset.chunks) > 0
