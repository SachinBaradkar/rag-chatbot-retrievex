"""
Embedding module — wraps sentence-transformers so we never call a paid API.
Model is downloaded once and cached in ~/.cache/huggingface.
"""

from __future__ import annotations
import logging
from typing import List

from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

from app.config.settings import EMBEDDING_MODEL, EMBEDDING_DEVICE

logger = logging.getLogger(__name__)

_model_cache: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str) -> SentenceTransformer:
    if model_name not in _model_cache:
        logger.info("Loading embedding model: %s", model_name)
        _model_cache[model_name] = SentenceTransformer(model_name, device=EMBEDDING_DEVICE)
    return _model_cache[model_name]


class LocalEmbeddings(Embeddings):
    """LangChain-compatible embeddings using a local sentence-transformer model."""

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model = _get_model(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        vector = self._model.encode([text], show_progress_bar=False, convert_to_numpy=True)
        return vector[0].tolist()


def get_embeddings() -> LocalEmbeddings:
    return LocalEmbeddings()
