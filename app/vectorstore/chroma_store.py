"""
Vector store — ChromaDB persisted locally.
Supports add, search, delete, and clear operations.
"""

from __future__ import annotations
import logging
import uuid
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config.settings import VECTORDB_DIR, CHROMA_COLLECTION, TOP_K, SIMILARITY_THRESHOLD
from app.embeddings.embedder import get_embeddings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=str(VECTORDB_DIR),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = get_embeddings()
        logger.info("VectorStore ready — collection: %s", CHROMA_COLLECTION)

    # ── Write ─────────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not chunks:
            return 0
        texts     = [c["text"]     for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids       = [str(uuid.uuid4()) for _ in chunks]
        vectors   = self._embedder.embed_documents(texts)
        self._collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)
        logger.info("Added %d chunks to vector store", len(chunks))
        return len(chunks)

    def delete_by_source(self, source_name: str) -> int:
        results = self._collection.get(where={"source": source_name})
        ids = results.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
            logger.info("Deleted %d chunks for source: %s", len(ids), source_name)
        return len(ids)

    def clear_all(self) -> None:
        self._client.delete_collection(CHROMA_COLLECTION)
        self._collection = self._client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store cleared")

    # ── Read ──────────────────────────────────────────────────────────────────

    def similarity_search(
        self,
        query: str,
        k: int = TOP_K,
        filter_source: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if self._collection.count() == 0:
            return []

        query_vector = self._embedder.embed_query(query)
        where = {"source": filter_source} if filter_source else None

        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, self._collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, raw_dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Store raw distance; UI will not show score percentage
            hits.append({"text": doc, "metadata": meta, "score": float(raw_dist)})

        # Sort by distance ascending (lower = more similar)
        hits.sort(key=lambda x: x["score"])
        # Keep only top-k above threshold (raw_dist < 1.0 means some similarity)
        hits = [h for h in hits if h["score"] < (1.0 - SIMILARITY_THRESHOLD + 1.0)]
        return hits[:k]

    def get_all_sources(self) -> List[str]:
        if self._collection.count() == 0:
            return []
        results = self._collection.get(include=["metadatas"])
        sources = {m.get("source", "") for m in results["metadatas"]}
        return sorted(s for s in sources if s)

    def total_chunks(self) -> int:
        return self._collection.count()

    def chunks_per_source(self) -> Dict[str, int]:
        if self._collection.count() == 0:
            return {}
        results = self._collection.get(include=["metadatas"])
        counts: Dict[str, int] = {}
        for m in results["metadatas"]:
            s = m.get("source", "unknown")
            counts[s] = counts.get(s, 0) + 1
        return counts


_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
