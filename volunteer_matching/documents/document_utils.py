"""
documents/document_utils.py
───────────────────────────
Utility helpers for Phase 11 OCR/document intelligence.

The helpers are intentionally conservative: OCR text is cleaned, capped, and
previewed safely because OCR output can be noisy or inaccurate.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
SUPPORTED_PDF_EXTS = {".pdf"}
MAX_EXTRACTED_TEXT_CHARS = 12000
MAX_PREVIEW_CHARS = 1800


def detect_file_type(file_path: str | Path) -> str:
    """Return 'pdf', 'image', or 'unsupported' based on file extension."""
    ext = Path(file_path or "").suffix.lower()
    if ext in SUPPORTED_PDF_EXTS:
        return "pdf"
    if ext in SUPPORTED_IMAGE_EXTS:
        return "image"
    return "unsupported"


def truncate_text(text: Any, limit: int = MAX_EXTRACTED_TEXT_CHARS) -> str:
    """Safely truncate text to a maximum number of characters."""
    if text is None:
        return ""
    value = str(text)
    if limit <= 0:
        return ""
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)].rstrip() + "..."


def clean_extracted_text(text: Any) -> str:
    """Clean OCR/PDF extracted text without inventing or changing meaning."""
    if text is None:
        return ""
    value = str(text).replace("\x00", " ")
    value = value.replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = value.strip()
    return truncate_text(value, MAX_EXTRACTED_TEXT_CHARS)


def safe_text_preview(text: Any, limit: int = MAX_PREVIEW_CHARS) -> str:
    """Return a Streamlit-safe preview of OCR text."""
    preview = clean_extracted_text(text)
    preview = truncate_text(preview, limit)
    return preview.replace("<", "&lt;").replace(">", "&gt;")
