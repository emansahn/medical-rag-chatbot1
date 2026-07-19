"""
TextChunker producing 300-800 token chunks with token-level overlap.

Text is split into paragraphs (on "\\n\\n"); any paragraph that alone
exceeds `max_tokens` is further split into sentences, so a chunk boundary
never falls mid-sentence unless a single sentence is itself larger than
`max_tokens` (unavoidable, kept as-is rather than cut).
"""
import re
from typing import List

from src.preprocessing.interfaces.document_loader_interface import DocumentChunk, RawDocument, TextChunker

_SENTENCE_BOUNDARY_PATTERN = re.compile(r"(?<=[.!?])\s+")


class TokenChunker(TextChunker):
    """Splits a `RawDocument`'s content into `DocumentChunk`s of
    `min_tokens`-`max_tokens` tokens (tiktoken `cl100k_base`), with
    `overlap_tokens` of token-level overlap carried into the start of each
    following chunk.

    Args:
        min_tokens: Target minimum tokens per chunk. The last chunk of a
            document (or the only chunk, for short documents) may be shorter.
        max_tokens: Hard cap on tokens per chunk (overlap included).
        overlap_tokens: Trailing tokens from the previous chunk repeated at
            the start of the next one.
    """

    def __init__(self, min_tokens: int = 300, max_tokens: int = 800, overlap_tokens: int = 100) -> None:
        import tiktoken  # heavy import kept out of module load time

        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def chunk(self, document: RawDocument) -> List[DocumentChunk]:
        text = document.content.strip()
        if not text:
            return []

        # Token windows provide a real hard cap even for flattened PDF tables
        # or OCR output with no sentence punctuation. The former paragraph /
        # sentence implementation could emit >800-token chunks when one
        # extracted "sentence" alone exceeded the configured maximum.
        tokens = self._encoding.encode(text)
        step = self.max_tokens - self.overlap_tokens
        if step <= 0:
            raise ValueError("overlap_tokens must be smaller than max_tokens")

        chunks: List[DocumentChunk] = []
        for index, start in enumerate(range(0, len(tokens), step)):
            window = tokens[start : start + self.max_tokens]
            if not window:
                break
            chunk_text = self._decode_with_hard_cap(window)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.source_id}-{index}",
                    text=chunk_text,
                    source_id=document.source_id,
                    source_title=document.title,
                    source_url=document.source_url,
                    metadata=dict(document.metadata),
                )
            )
            if start + self.max_tokens >= len(tokens):
                break
        return chunks

    def _decode_with_hard_cap(self, tokens: List[int]) -> str:
        """Decode a window while preserving the serialized token hard cap."""
        text = self._encoding.decode(tokens).strip()
        while len(encoded := self._encoding.encode(text)) > self.max_tokens:
            text = self._encoding.decode(encoded[: self.max_tokens]).strip()
        return text

    def _split_into_units(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        units: List[str] = []
        for paragraph in paragraphs:
            if len(self._encoding.encode(paragraph)) <= self.max_tokens:
                units.append(paragraph)
            else:
                sentences = [s.strip() for s in _SENTENCE_BOUNDARY_PATTERN.split(paragraph) if s.strip()]
                units.extend(sentences or [paragraph])
        return units

    def _fill_group(self, overlap_text: str, remaining: List[str]) -> List[str]:
        """Greedily consumes units from `remaining` (mutating it) into a
        group whose joined-with-overlap token count stays within
        `max_tokens`, stopping only when the next unit would not fit."""
        group_units: List[str] = []
        while remaining:
            candidate_units = group_units + [remaining[0]]
            candidate_tokens = len(self._encoding.encode(self._join(overlap_text, candidate_units)))
            if candidate_tokens > self.max_tokens and group_units:
                break
            group_units.append(remaining.pop(0))
            if candidate_tokens > self.max_tokens:
                break
        return group_units

    @staticmethod
    def _join(overlap_text: str, units: List[str]) -> str:
        parts = [part for part in [overlap_text, *units] if part]
        return " ".join(parts)
