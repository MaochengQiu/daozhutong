import math
import re
from collections import Counter
from typing import List, Tuple

from app.qa.doc_processor import DocChunk


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", text.lower())


class Retriever:
    def __init__(self, chunks: List[DocChunk]):
        self.chunks = chunks
        self._vectors = [Counter(_tokenize(ch.text)) for ch in chunks]

    @staticmethod
    def _cosine_sim(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        dot = sum(a[k] * b[k] for k in a.keys() & b.keys())
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocChunk, float]]:
        q_vec = Counter(_tokenize(query))
        scored: List[Tuple[DocChunk, float]] = []
        for ch, vec in zip(self.chunks, self._vectors):
            scored.append((ch, self._cosine_sim(q_vec, vec)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
