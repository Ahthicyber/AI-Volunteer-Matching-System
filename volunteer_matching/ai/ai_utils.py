"""
ai/ai_utils.py
──────────────
Small safety helpers for optional AI text generation.

These helpers keep LLM output concise and Streamlit-safe without changing any
matching, ML, approval, or application decision logic.
"""

from __future__ import annotations

import re
from typing import Any


DEFAULT_AI_FALLBACK = (
    "AI explanation temporarily unavailable. The deterministic recommendation "
    "score remains the authoritative result."
)


def truncate_text(value: Any, limit: int = 1200) -> str:
    """Return a stripped string capped to a safe character length."""
    if value is None:
        return ""
    text = str(value).strip()
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    return text[: max(limit - 3, 0)].rstrip() + "..."


def truncate_response(value: Any, max_words: int = 220, max_chars: int = 1400) -> str:
    """Limit AI responses to a presentation-friendly length."""
    text = truncate_text(value, max_chars)
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(" .,;:") + "..."


def remove_unwanted_markdown(value: Any) -> str:
    """Remove heavy markdown/HTML/code formatting from explanation text."""
    text = "" if value is None else str(value)

    # Remove fenced code blocks and inline code markers; explanations should not be code.
    text = re.sub(r"```[a-zA-Z0-9_-]*", "", text)
    text = text.replace("```", "")
    text = text.replace("`", "")

    # Remove markdown headings/emphasis that often look noisy inside Streamlit cards.
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"(\*\*|__|~~)", "", text)

    # Remove raw HTML tags while preserving the contained text.
    text = re.sub(r"<[^>]+>", "", text)

    # Normalize bullets to simple hyphen bullets.
    text = re.sub(r"^\s*[•*]\s+", "- ", text, flags=re.MULTILINE)

    return text.strip()


def clean_ai_response(value: Any, max_chars: int = 1200) -> str:
    """Normalize whitespace and remove risky/irrelevant markup from AI text."""
    text = truncate_text(value, max_chars)
    if not text:
        return ""

    text = remove_unwanted_markdown(text)

    # Collapse excessive blank lines/spaces while preserving short bullet lists.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sanitize_ai_response(value: Any, max_words: int = 230, max_chars: int = 1400) -> str:
    """Prepare an AI explanation for safe, concise Streamlit display."""
    text = clean_ai_response(value, max_chars=max_chars)
    text = truncate_response(text, max_words=max_words, max_chars=max_chars)
    # Avoid accidental raw HTML rendering if a developer later uses unsafe HTML.
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text.strip()


def sanitize_markdown(value: Any, max_chars: int = 1200) -> str:
    """Backward-compatible light markdown sanitization helper."""
    return sanitize_ai_response(value, max_chars=max_chars)


def fallback_response(message: str | None = None) -> str:
    """Return a consistent fallback message for unavailable AI features."""
    return sanitize_ai_response(message or DEFAULT_AI_FALLBACK, max_words=80, max_chars=500)


def compact_dict(data: dict[str, Any] | None, max_value_chars: int = 250) -> dict[str, str]:
    """Create a prompt-safe dictionary with short string values."""
    if not data:
        return {}
    return {str(k): truncate_text(v, max_value_chars) for k, v in data.items()}
