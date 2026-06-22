"""
Basic smoke tests — run with:  python -m pytest tests/ -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def test_settings_import():
    from app.config.settings import CHUNK_SIZE, TOP_K, SUPPORTED_EXTENSIONS
    assert CHUNK_SIZE > 0
    assert TOP_K > 0
    assert ".pdf" in SUPPORTED_EXTENSIONS


def test_chunker():
    from app.ingestion.chunker import chunk_pages
    pages = [
        {"text": "Hello world. " * 100, "metadata": {"source": "test.txt", "page": 1, "file_type": "txt"}}
    ]
    chunks = chunk_pages(pages)
    assert len(chunks) > 0
    for c in chunks:
        assert "text" in c
        assert "metadata" in c
        assert c["metadata"]["source"] == "test.txt"


def test_text_loader(tmp_path):
    from app.ingestion.loaders import load_text
    f = tmp_path / "test.txt"
    f.write_text("This is a test document with some content.")
    pages = load_text(f)
    assert len(pages) == 1
    assert "test" in pages[0]["text"].lower()


def test_helpers():
    from app.utils.helpers import truncate, safe_filename
    long_text = "word " * 200
    result = truncate(long_text, 100)
    assert len(result) <= 110  # some leeway for ellipsis
    assert safe_filename("file<>name.pdf") == "file__name.pdf"


def test_embeddings():
    """Test that embeddings produce vectors of correct shape."""
    from app.embeddings.embedder import get_embeddings
    emb = get_embeddings()
    vec = emb.embed_query("test sentence")
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert isinstance(vec[0], float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
