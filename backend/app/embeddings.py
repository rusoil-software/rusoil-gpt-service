from __future__ import annotations

from typing import Iterable, List, Tuple
import math
import hashlib


class EmbeddingEngine:
    """A simple, deterministic embedding engine used for tests and examples.

    It generates a fixed-length numeric embedding vector by hashing input text and
    deriving floats from the hash bytes. This avoids external dependencies while
    providing a reproducible embedding for examples and tests.
    """

    def __init__(self, dim: int = 8, max_input_chars: int = 10000):
        self.dim = dim
        self.max_input_chars = max_input_chars

    def encode(self, text: str) -> List[float]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if len(text) > self.max_input_chars:
            raise ValueError("input too large")
        h = hashlib.blake2b(text.encode('utf-8'), digest_size=64)
        data = h.digest()
        # produce dim floats between -1 and 1
        out = []
        for i in range(self.dim):
            idx = i * (len(data) // self.dim)
            b = data[idx: idx + 4]
            v = int.from_bytes(b, 'big', signed=False)
            f = (v % 10000) / 5000.0 - 1.0
            out.append(f)
        return out

    def encode_batch(self, inputs: Iterable[str]) -> List[List[float]]:
        return [self.encode(t) for t in inputs]


# Chunking helper

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 0) -> List[str]:
    """Split text into chunks of up to chunk_size with optional overlap.

    Returns list of chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap
    return chunks
*** End Patch