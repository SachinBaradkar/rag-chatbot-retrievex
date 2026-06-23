"""
Ingestion pipeline — loads a file, chunks it, stores embeddings.
Handles duplicate detection via SHA-256 hash stored in metadata.
"""

from __future__ import annotations
import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.config.settings import UPLOAD_DIR, DATA_DIR, SUPPORTED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from app.ingestion.loaders  import load_document
from app.ingestion.chunker  import chunk_pages
from app.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)

MANIFEST_PATH = DATA_DIR / "manifest.json"


# ── Manifest (duplicate detection) ───────────────────────────────────────────

def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text())
        except Exception:
            pass
    return {}


def _save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class IngestionResult:
    filename: str
    success: bool
    chunks_added: int = 0
    pages_found: int = 0
    duplicate: bool = False
    error: Optional[str] = None


# ── Main pipeline ─────────────────────────────────────────────────────────────

def ingest_file(uploaded_file_obj, filename: str) -> IngestionResult:
    """
    Accept a file-like object (from Streamlit uploader) and ingest it.
    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return IngestionResult(filename=filename, success=False,
                               error=f"Unsupported file type: {ext}")

    # Save to uploads dir
    dest = UPLOAD_DIR / filename
    try:
        with open(dest, "wb") as f:
            f.write(uploaded_file_obj.read()
                    if hasattr(uploaded_file_obj, "read")
                    else uploaded_file_obj)
    except Exception as e:
        return IngestionResult(filename=filename, success=False,
                               error=f"Could not save file: {e}")

    # Size check
    size_mb = dest.stat().st_size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        dest.unlink(missing_ok=True)
        return IngestionResult(filename=filename, success=False,
                               error=f"File exceeds {MAX_UPLOAD_SIZE_MB} MB limit")

    # Duplicate check
    file_hash = _file_hash(dest)
    manifest = _load_manifest()
    if file_hash in manifest:
        return IngestionResult(filename=filename, success=True,
                               duplicate=True,
                               chunks_added=manifest[file_hash].get("chunks", 0))

    # Load
    pages = load_document(dest)
    if not pages:
        dest.unlink(missing_ok=True)
        return IngestionResult(filename=filename, success=False,
                               error="No text could be extracted from this file.")

    # Chunk
    chunks = chunk_pages(pages)
    if not chunks:
        dest.unlink(missing_ok=True)
        return IngestionResult(filename=filename, success=False,
                               error="No chunks generated — file may be empty.")

    # Store
    store = get_vector_store()
    added = store.add_chunks(chunks)

    # Update manifest
    manifest[file_hash] = {"filename": filename, "chunks": added, "pages": len(pages)}
    _save_manifest(manifest)

    return IngestionResult(
        filename=filename,
        success=True,
        chunks_added=added,
        pages_found=len(pages),
    )


def delete_document(filename: str) -> bool:
    """Remove a document's chunks from the store and its file from disk."""
    store = get_vector_store()
    deleted = store.delete_by_source(filename)

    file_path = UPLOAD_DIR / filename
    file_path.unlink(missing_ok=True)

    # Remove from manifest
    manifest = _load_manifest()
    manifest = {h: v for h, v in manifest.items() if v.get("filename") != filename}
    _save_manifest(manifest)

    logger.info("Deleted %s (%d chunks removed)", filename, deleted)
    return deleted > 0


def clear_knowledge_base() -> None:
    """Wipe everything — vector store, uploads, manifest."""
    store = get_vector_store()
    store.clear_all()

    for f in UPLOAD_DIR.iterdir():
        # Only delete actual files with supported extensions, skip dirs and hidden files
        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                f.unlink()
            except Exception as e:
                logger.warning("Could not delete %s: %s", f.name, e)

    _save_manifest({})
    logger.info("Knowledge base cleared")


def list_uploaded_documents() -> List[dict]:
    """Return info about each ingested document."""
    store = get_vector_store()
    counts = store.chunks_per_source()
    manifest = _load_manifest()

    # Build name → page count from manifest
    name_to_pages = {v["filename"]: v.get("pages", 0) for v in manifest.values()}

    docs = []
    for source, chunk_count in counts.items():
        docs.append({
            "filename": source,
            "chunks": chunk_count,
            "pages": name_to_pages.get(source, "?"),
            "size": _get_file_size(UPLOAD_DIR / source),
        })
    return sorted(docs, key=lambda d: d["filename"])


def _get_file_size(path: Path) -> str:
    if not path.exists():
        return "N/A"
    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size/1024:.1f} KB"
    else:
        return f"{size/1024**2:.1f} MB"
