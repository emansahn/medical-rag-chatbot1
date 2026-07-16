"""
Mock implementations of DocumentProvider / ChunkProvider / DatasetLoader.

Return small, realistic sample data so anything depending on these
interfaces — the analytics dashboard, ingestion test scripts, future admin
tooling — works correctly before Person 1 has collected a single real
document. Zero external dependencies (no pypdf, no bs4).
"""
from typing import List

from src.preprocessing.interfaces.data_provider_interface import ChunkProvider, Dataset, DatasetLoader, DocumentProvider
from src.preprocessing.interfaces.document_loader_interface import DocumentChunk, RawDocument

_SAMPLE_DOCUMENTS: List[RawDocument] = [
    RawDocument(
        source_id="sample-diabete-001",
        title="Guide de prévention du diabète (exemple)",
        content="Le diabète de type 2 peut être prévenu par une alimentation équilibrée et une activité physique régulière...",
        source_url="https://www.sante.gov.ma/exemple-diabete",
        metadata={"institution": "Ministère de la Santé (exemple)", "language": "fr"},
    ),
    RawDocument(
        source_id="sample-vaccination-001",
        title="Calendrier de vaccination national (exemple)",
        content="La vaccination reste l'un des moyens les plus efficaces de prévenir les maladies infectieuses...",
        source_url="https://www.emro.who.int/exemple-vaccination",
        metadata={"institution": "OMS Maroc (exemple)", "language": "fr"},
    ),
]

_SAMPLE_CHUNKS: List[DocumentChunk] = [
    DocumentChunk(
        chunk_id="sample-diabete-001-c1",
        text="Le diabète de type 2 peut être prévenu par une alimentation équilibrée et une activité physique régulière (exemple).",
        source_id="sample-diabete-001",
        source_title="Guide de prévention du diabète (exemple)",
        source_url="https://www.sante.gov.ma/exemple-diabete",
    ),
    DocumentChunk(
        chunk_id="sample-vaccination-001-c1",
        text="La vaccination reste l'un des moyens les plus efficaces de prévenir les maladies infectieuses (exemple).",
        source_id="sample-vaccination-001",
        source_title="Calendrier de vaccination national (exemple)",
        source_url="https://www.emro.who.int/exemple-vaccination",
    ),
]


class MockDocumentProvider(DocumentProvider):
    def list_documents(self) -> List[RawDocument]:
        return list(_SAMPLE_DOCUMENTS)

    def count(self) -> int:
        return len(_SAMPLE_DOCUMENTS)


class MockChunkProvider(ChunkProvider):
    def list_chunks(self) -> List[DocumentChunk]:
        return list(_SAMPLE_CHUNKS)

    def count(self) -> int:
        return len(_SAMPLE_CHUNKS)


class MockDatasetLoader(DatasetLoader):
    def load(self) -> Dataset:
        return Dataset(documents=list(_SAMPLE_DOCUMENTS), chunks=list(_SAMPLE_CHUNKS))
