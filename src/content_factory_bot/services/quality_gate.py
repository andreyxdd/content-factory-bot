"""Internal QUALITY GATE pass (Generic / Rhythm / Specificity / Anti-slop)."""

from __future__ import annotations

import logging
from typing import Protocol

from content_factory_bot.llm.client import LLMClient
from content_factory_bot.services.prompt_guard import wrap_user_content

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class ChatClient(Protocol):
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict | None = None,
    ) -> str: ...


async def apply_quality_gate(
    *,
    system_prompt: str,
    draft_text: str,
    style_card: str,
    content_language: str,
    client: ChatClient | None = None,
    max_retries: int = MAX_RETRIES,
) -> tuple[str, int]:
    """
    Run internal critics and return (final_text, retry_count).
    User never sees critic output.
    """
    llm = client or LLMClient.from_settings()
    current = draft_text
    retries = 0
    gate_system = (
        f"{system_prompt}\n\n"
        "You are an internal editor. Apply QUALITY GATE silently:\n"
        "1. Generic detector — remove AI filler.\n"
        "2. Rhythm — break 3+ same-length sentence streaks.\n"
        "3. Specificity — keep first-person + concrete detail.\n"
        "4. Anti-slop — remove empty slogans.\n"
        "Return ONLY the revised post text. No commentary."
    )
    user = (
        f"<style_card>\n{style_card}\n</style_card>\n"
        f"Target language locale: {content_language}\n\n"
        f"{wrap_user_content('draft', current)}"
    )
    for attempt in range(max_retries + 1):
        try:
            revised = await llm.chat(
                [
                    {"role": "system", "content": gate_system},
                    {"role": "user", "content": user},
                ]
            )
            revised = revised.strip()
            if not revised:
                break
            if revised == current:
                break
            current = revised
            if attempt < max_retries:
                retries += 1
                user = (
                    f"<style_card>\n{style_card}\n</style_card>\n"
                    f"Target language locale: {content_language}\n\n"
                    f"{wrap_user_content('draft', current)}"
                )
        except Exception:
            logger.exception("quality_gate attempt=%s failed", attempt)
            break
    return current, retries
