"""
Retrieval — similarity search + optional cross-encoder reranking.
Returns ranked, deduplicated chunks with metadata and scores.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from app.config.settings import TOP_K
from app.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)

# Optional reranker — gracefully skips if not installed
try:
    from sentence_transformers import CrossEncoder
    _RERANKER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    RERANKING_AVAILABLE = True
    logger.info("Cross-encoder reranker loaded")
except Exception:
    RERANKING_AVAILABLE = False
    logger.info("Reranker not available — using raw similarity scores")


def retrieve(
    query: str,
    k: int = TOP_K,
    rerank: bool = True,
    filter_source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Returns top-k chunks relevant to the query.
    Each chunk: {text, metadata, score, rerank_score (if reranking)}
    """
    store = get_vector_store()
    # Fetch more candidates if we'll rerank
    fetch_k = min(k * 3, 20) if (rerank and RERANKING_AVAILABLE) else k
    hits = store.similarity_search(query, k=fetch_k, filter_source=filter_source)

    if not hits:
        return []

    if rerank and RERANKING_AVAILABLE and len(hits) > 1:
        pairs = [(query, h["text"]) for h in hits]
        scores = _RERANKER.predict(pairs)
        for hit, rs in zip(hits, scores):
            hit["rerank_score"] = round(float(rs), 4)
        hits.sort(key=lambda x: x["rerank_score"], reverse=True)

    return hits[:k]


def format_context(hits: List[Dict[str, Any]]) -> str:
    """Build the context string injected into the LLM prompt."""
    parts = []
    for i, h in enumerate(hits, 1):
        meta = h["metadata"]
        source = meta.get("source", "unknown")
        page   = meta.get("page", "?")
        parts.append(f"[Source {i}: {source}, Page {page}]\n{h['text']}")
    return "\n\n---\n\n".join(parts)
