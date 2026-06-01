"""Compose effective system prompts for content generation."""

from __future__ import annotations

MAX_SYSTEM_PROMPT_ADDITION_LEN = 2000

_ADDITION_HEADER = "# CREATOR ADDITIONS\n"


def compose_system_prompt(base: str, addition: str | None) -> str:
    """Append user-defined instructions after the onboarding system prompt."""
    extra = (addition or "").strip()
    if not extra:
        return base
    return f"{base.rstrip()}\n\n{_ADDITION_HEADER}{extra}"


def validate_system_prompt_addition(text: str) -> str | None:
    """Return error key if invalid, else None."""
    if len(text.strip()) > MAX_SYSTEM_PROMPT_ADDITION_LEN:
        return "too_long"
    return None
