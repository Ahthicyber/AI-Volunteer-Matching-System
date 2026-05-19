"""Optional email notification infrastructure.

This phase intentionally does not require SMTP. The wrapper is a safe placeholder
for future expansion and always fails gracefully when email is disabled.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def is_email_enabled() -> bool:
    """Return True only when future SMTP settings are explicitly enabled."""
    return os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def send_email_notification(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    """Placeholder email sender. Never breaks the app if email is disabled."""
    if not is_email_enabled():
        return False, "Email notifications are disabled. In-app notifications were used instead."
    logger.info("Email notification placeholder called for %s with subject %s", to_email, subject)
    return False, "SMTP email delivery is not configured in this phase."
