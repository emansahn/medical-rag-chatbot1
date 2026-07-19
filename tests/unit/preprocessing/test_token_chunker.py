"""Unit tests for TokenChunker."""
import tiktoken

from src.preprocessing.chunking.token_chunker import TokenChunker
from src.preprocessing.interfaces.document_loader_interface import DocumentChunk, RawDocument, TextChunker

_ENCODING = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    return len(_ENCODING.encode(text))


def _make_document(content: str, source_id: str = "doc-test") -> RawDocument:
    return RawDocument(
        source_id=source_id,
        title="Guide de test",
        content=content,
        source_url="https://example.org/doc-test",
        metadata={"institution": "Test"},
    )


def _make_long_document(num_paragraphs: int = 60) -> RawDocument:
    paragraphs = [
        f"Ceci est la phrase numero {i} du document de test sur la sante publique au Maroc. "
        f"Elle contient suffisamment de mots pour simuler un paragraphe medical realiste "
        f"avec du contenu varie numero {i}."
        for i in range(num_paragraphs)
    ]
    return _make_document("\n\n".join(paragraphs))


def test_long_document_chunks_stay_within_min_max_tokens():
    chunker = TokenChunker(min_tokens=300, max_tokens=800, overlap_tokens=100)
    document = _make_long_document()

    chunks = chunker.chunk(document)

    assert len(chunks) > 1
    for chunk in chunks[:-1]:
        token_count = _token_count(chunk.text)
        assert chunker.min_tokens <= token_count <= chunker.max_tokens

    last_token_count = _token_count(chunks[-1].text)
    assert last_token_count <= chunker.max_tokens


def test_consecutive_chunks_overlap():
    chunker = TokenChunker(min_tokens=300, max_tokens=800, overlap_tokens=100)
    document = _make_long_document()

    chunks = chunker.chunk(document)
    assert len(chunks) > 1

    for previous, following in zip(chunks, chunks[1:]):
        tail_snippet = previous.text[-50:]
        assert tail_snippet in following.text[:600]


def test_short_document_returns_single_chunk_with_all_content():
    chunker = TokenChunker()
    text = "Le paracetamol est un antalgique courant."
    document = _make_document(text)

    chunks = chunker.chunk(document)

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert _token_count(text) < chunker.min_tokens


def test_source_metadata_is_propagated_to_every_chunk():
    chunker = TokenChunker()
    document = _make_long_document()

    chunks = chunker.chunk(document)

    assert len(chunks) > 1
    for chunk in chunks:
        assert isinstance(chunk, DocumentChunk)
        assert chunk.source_id == document.source_id
        assert chunk.source_title == document.title
        assert chunk.source_url == document.source_url


def test_chunk_ids_are_unique_and_deterministic():
    chunker = TokenChunker()
    document = _make_long_document()

    first_run = chunker.chunk(document)
    second_run = chunker.chunk(document)

    first_ids = [c.chunk_id for c in first_run]
    second_ids = [c.chunk_id for c in second_run]

    assert len(first_ids) == len(set(first_ids))
    assert first_ids == second_ids


def test_empty_content_returns_empty_list():
    chunker = TokenChunker()
    assert isinstance(chunker, TextChunker)

    document = _make_document("")
    assert chunker.chunk(document) == []


def test_single_unpunctuated_pdf_block_never_exceeds_hard_cap():
    chunker = TokenChunker(min_tokens=100, max_tokens=450, overlap_tokens=75)
    document = _make_document("tableaucellule " * 2000)

    chunks = chunker.chunk(document)

    assert len(chunks) > 1
    assert all(_token_count(chunk.text) <= 450 for chunk in chunks)


def test_boundary_whitespace_cannot_exceed_the_serialized_cap():
    chunker = TokenChunker(min_tokens=10, max_tokens=64, overlap_tokens=8)
    document = _make_document(" données médicales\n" * 250)

    chunks = chunker.chunk(document)

    assert chunks
    assert all(_token_count(chunk.text) <= 64 for chunk in chunks)
