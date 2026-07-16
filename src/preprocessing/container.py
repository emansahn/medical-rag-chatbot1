"""
Data provider container — decides Mock vs Real, controlled by `DATA_MODE`.

    DATA_MODE=mock (default) -> Mock*Provider, small sample data, no dependency
                                  on data/chunks/ existing yet.
    DATA_MODE=real            -> Real*Provider, reads data/chunks/ and
                                  data/processed/ produced by Person 1's pipeline.
"""
from src.core.config import settings
from src.core.logging_config import get_logger
from src.preprocessing.interfaces.data_provider_interface import ChunkProvider, DatasetLoader, DocumentProvider

logger = get_logger(__name__)

_document_provider: "DocumentProvider | None" = None
_chunk_provider: "ChunkProvider | None" = None
_dataset_loader: "DatasetLoader | None" = None


def get_document_provider() -> DocumentProvider:
    global _document_provider
    if _document_provider is None:
        if settings.data_mode == "real":
            from src.preprocessing.providers.real_providers import RealDocumentProvider

            _document_provider = RealDocumentProvider()
        else:
            from src.preprocessing.providers.mock_providers import MockDocumentProvider

            _document_provider = MockDocumentProvider()
        logger.info("DocumentProvider ready (data_mode=%s)", settings.data_mode)
    return _document_provider


def get_chunk_provider() -> ChunkProvider:
    global _chunk_provider
    if _chunk_provider is None:
        if settings.data_mode == "real":
            from src.preprocessing.providers.real_providers import RealChunkProvider

            _chunk_provider = RealChunkProvider()
        else:
            from src.preprocessing.providers.mock_providers import MockChunkProvider

            _chunk_provider = MockChunkProvider()
        logger.info("ChunkProvider ready (data_mode=%s)", settings.data_mode)
    return _chunk_provider


def get_dataset_loader() -> DatasetLoader:
    global _dataset_loader
    if _dataset_loader is None:
        if settings.data_mode == "real":
            from src.preprocessing.providers.real_providers import RealDatasetLoader

            _dataset_loader = RealDatasetLoader()
        else:
            from src.preprocessing.providers.mock_providers import MockDatasetLoader

            _dataset_loader = MockDatasetLoader()
        logger.info("DatasetLoader ready (data_mode=%s)", settings.data_mode)
    return _dataset_loader
