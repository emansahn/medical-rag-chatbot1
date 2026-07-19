"""Production data-provider dependency container."""
from src.core.logging_config import get_logger
from src.preprocessing.interfaces.data_provider_interface import ChunkProvider, DatasetLoader, DocumentProvider

logger = get_logger(__name__)

_document_provider: "DocumentProvider | None" = None
_chunk_provider: "ChunkProvider | None" = None
_dataset_loader: "DatasetLoader | None" = None


def get_document_provider() -> DocumentProvider:
    global _document_provider
    if _document_provider is None:
        from src.preprocessing.providers.real_providers import RealDocumentProvider

        _document_provider = RealDocumentProvider()
        logger.info("Production DocumentProvider ready")
    return _document_provider


def get_chunk_provider() -> ChunkProvider:
    global _chunk_provider
    if _chunk_provider is None:
        from src.preprocessing.providers.real_providers import RealChunkProvider

        _chunk_provider = RealChunkProvider()
        logger.info("Production ChunkProvider ready")
    return _chunk_provider


def get_dataset_loader() -> DatasetLoader:
    global _dataset_loader
    if _dataset_loader is None:
        from src.preprocessing.providers.real_providers import RealDatasetLoader

        _dataset_loader = RealDatasetLoader()
        logger.info("Production DatasetLoader ready")
    return _dataset_loader
