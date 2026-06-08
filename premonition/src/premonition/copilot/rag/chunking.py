"""Document chunking for RAG."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    index: int
    start_char: int
    end_char: int


class DocumentChunker:
    """Split documents into overlapping chunks."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[TextChunk]:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []
        chunks: list[TextChunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(TextChunk(text=chunk_text, index=idx, start_char=start, end_char=end))
            if end >= len(text):
                break
            start = end - self.overlap
            idx += 1
        return chunks
