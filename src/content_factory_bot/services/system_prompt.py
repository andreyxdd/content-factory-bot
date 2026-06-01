"""Compose effective system prompts for content generation."""

from __future__ import annotations

MAX_SYSTEM_PROMPT_ADDITION_LEN = 2000

_CREATOR_HEADER = "# CREATOR ADDITIONS\n"
_SESSION_HEADER = "# SESSION ADDITIONS\n"


def compose_system_prompt(
    base: str,
    *,
    creator_addition: str | None = None,
    session_addition: str | None = None,
) -> str:
    """Append creator- and session-scoped instructions after the base system prompt."""
    out = base.rstrip()
    creator = (creator_addition or "").strip()
    session = (session_addition or "").strip()
    if creator:
        out = f"{out}\n\n{_CREATOR_HEADER}{creator}"
    if session:
        out = f"{out}\n\n{_SESSION_HEADER}{session}"
    return out


def validate_system_prompt_addition(text: str) -> str | None:
    """Return error key if invalid, else None."""
    if len(text.strip()) > MAX_SYSTEM_PROMPT_ADDITION_LEN:
        return "too_long"
    return None
