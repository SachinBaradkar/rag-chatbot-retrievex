"""
Chunking — splits raw pages into retrieval-sized chunks.
Preserves metadata (source, page, etc.) from each page.
"""

from __future__ import annotations
from typing import List, Dict, Any

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config.settings import CHUNK_SIZE, CHUNK_OVERLAP

RawPage  = Dict[str, Any]
Chunk    = Dict[str, Any]  # {"text": str, "metadata": dict}


def chunk_pages(pages: List[RawPage]) -> List[Chunk]:
    """Split pages into smaller, overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: List[Chunk] = []
    for page in pages:
        text = page["text"]
        meta = page["metadata"]
        splits = splitter.split_text(text)
        for i, split in enumerate(splits):
            if split.strip():
                chunk_meta = {**meta, "chunk_index": i}
                chunks.append({"text": split.strip(), "metadata": chunk_meta})

    return chunks
