"""General-purpose utilities."""

from __future__ import annotations
import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stdout,
    )


def truncate(text: str, max_chars: int = 300) -> str:
    """Shorten long text for UI display."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + " …"


def safe_filename(name: str) -> str:
    """Remove dangerous characters from a filename."""
    import re
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name[:200]


def format_source_citation(metadata: dict, score: float) -> str:
    source = metadata.get("source", "unknown")
    page   = metadata.get("page", "?")
    sheet  = metadata.get("sheet", "")
    score_pct = f"{score*100:.0f}%"
    if sheet:
        return f"📄 **{source}** (Sheet: {sheet}) — Relevance: {score_pct}"
    return f"📄 **{source}** (Page {page}) — Relevance: {score_pct}"
