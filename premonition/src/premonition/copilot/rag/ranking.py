"""Retrieval ranking engine."""

from __future__ import annotations

import re

from premonition.copilot.rag.vector_store import SearchResult


class RetrievalRankingEngine:
    """Re-rank retrieval results with keyword boosting."""

    def rank(self, query: str, results: list[SearchResult], top_k: int = 5) -> list[SearchResult]:
        if not results:
            return []
        query_terms = set(re.findall(r"\w+", query.lower()))
        scored: list[tuple[SearchResult, float]] = []
        for result in results:
            text_terms = set(re.findall(r"\w+", result.document.text.lower()))
            overlap = len(query_terms & text_terms) / max(len(query_terms), 1)
            combined = result.score * 0.7 + overlap * 0.3
            scored.append((result, combined))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [SearchResult(document=r.document, score=s) for r, s in scored[:top_k]]
