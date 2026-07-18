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

        units = self._split_into_units(text)
        chunks: List[DocumentChunk] = []
        remaining = list(units)
        overlap_text = ""
        index = 0

        while remaining:
            group_units = self._fill_group(overlap_text, remaining)
            chunk_text = self._join(overlap_text, group_units)
            chunk_tokens = self._encoding.encode(chunk_text)

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

            if remaining and self.overlap_tokens > 0:
                tail_tokens = chunk_tokens[-self.overlap_tokens :]
                overlap_text = self._encoding.decode(tail_tokens)
            else:
                overlap_text = ""
            index += 1

        return chunks

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
