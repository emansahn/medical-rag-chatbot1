"""Unit tests for the production dependency-injection containers."""
from unittest.mock import patch

from src.preprocessing.container import get_chunk_provider, get_dataset_loader, get_document_provider
from src.preprocessing.interfaces.data_provider_interface import ChunkProvider, DatasetLoader, DocumentProvider
from src.rag.container import _build_service
from src.rag.interfaces.rag_service_interface import RAGAnswer, RAGService


class _FakeRealService(RAGService):
    def is_ready(self) -> bool:
        return True

    def answer_question(self, question: str, language: str = "fr") -> RAGAnswer:
        return RAGAnswer(answer=question, is_mock=False)


def test_container_builds_only_the_real_rag_service():
    fake = _FakeRealService()
    with patch(
        "src.rag.services.real_rag_service.RealRAGService", return_value=fake
    ) as constructor:
        assert _build_service() is fake
    constructor.assert_called_once_with()


def test_container_uses_real_data_providers():
    doc_provider = get_document_provider()
    chunk_provider = get_chunk_provider()
    dataset_loader = get_dataset_loader()

    assert isinstance(doc_provider, DocumentProvider)
    assert isinstance(chunk_provider, ChunkProvider)
    assert isinstance(dataset_loader, DatasetLoader)

    assert chunk_provider.count() > 0

    dataset = dataset_loader.load()
    assert len(dataset.chunks) > 0
