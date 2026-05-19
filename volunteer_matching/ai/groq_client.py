"""
ai/groq_client.py
─────────────────
Centralized, optional Groq API wrapper for Phase 10.1.

This module never raises raw Groq errors to Streamlit pages. It returns clean
text or safe fallback messages so the app remains runnable without an API key.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from utils.config import get_groq_api_key
from ai.ai_utils import clean_ai_response, fallback_response, truncate_text
from ai.prompts import AI_SYSTEM_GUARDRAILS

logger = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


try:
    from groq import Groq
except Exception:  # pragma: no cover - environment may not have groq installed yet
    Groq = None  # type: ignore


def is_groq_available() -> bool:
    """Return True when the Groq package and API key are both available."""
    return Groq is not None and get_groq_api_key() is not None


@lru_cache(maxsize=1)
def get_groq_client():
    """
    Initialize and cache the Groq client.

    Returns None if the package or API key is unavailable. Calling code should
    treat None as a normal optional-AI state, not an application error.
    """
    api_key = get_groq_api_key()
    if Groq is None:
        logger.info("Groq package is not installed. AI layer disabled.")
        return None
    if not api_key:
        logger.info("GROQ_API_KEY is not configured. AI layer disabled.")
        return None
    try:
        # The official client supports timeout at client initialization.
        return Groq(api_key=api_key, timeout=20.0)
    except Exception as exc:
        logger.warning("Could not initialize Groq client: %s", exc)
        return None


def generate_completion(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.4,
    max_tokens: int = 300,
) -> str:
    """
    Generate a concise Groq completion with full failure safety.

    Returns user-safe text in every case. It never raises API, network, timeout,
    rate-limit, invalid-key, or malformed-response exceptions to the UI.
    """
    if not prompt or not str(prompt).strip():
        return fallback_response("AI prompt was empty, so no response was generated.")

    client = get_groq_client()
    if client is None:
        return fallback_response(
            "Groq AI is not configured yet. Add GROQ_API_KEY to .env or Streamlit secrets to enable this optional explanation layer."
        )

    safe_system_prompt = truncate_text(system_prompt or AI_SYSTEM_GUARDRAILS, 2500)
    safe_prompt = truncate_text(prompt, 5000)

    try:
        response = client.chat.completions.create(
            model=DEFAULT_GROQ_MODEL,
            messages=[
                {"role": "system", "content": safe_system_prompt},
                {"role": "user", "content": safe_prompt},
            ],
            temperature=max(0.0, min(float(temperature), 1.0)),
            max_tokens=max(50, min(int(max_tokens), 800)),
        )

        content: Optional[str] = None
        if response and getattr(response, "choices", None):
            first_choice = response.choices[0]
            message = getattr(first_choice, "message", None)
            content = getattr(message, "content", None)

        cleaned = clean_ai_response(content, max_chars=1500)
        if not cleaned:
            return fallback_response("Groq returned an empty response. Please try again later.")
        return cleaned

    except Exception as exc:
        # Keep logs useful for developers while returning a clean UI message.
        logger.warning("Groq completion failed safely: %s", exc)
        return fallback_response(
            "Groq AI is currently unavailable. The app is still working normally, and deterministic recommendations remain unchanged."
        )
