"""Review step — short HTML critique before angle/draft menus when review_enabled."""

from __future__ import annotations

import logging
from typing import Any

from content_factory_bot.llm.client import LLMClient
from content_factory_bot.locale.telegram_html import format_review_message, parse_review_points

logger = logging.getLogger(__name__)

REVIEW_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "short_review",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
                "points": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        "required": ["label", "note"],
                        "additionalProperties": False,
                    },
                    "minItems": 2,
                    "maxItems": 3,
                }
            },
            "required": ["points"],
            "additionalProperties": False,
        },
    },
}


class ReviewStep:
    async def critique(
        self,
        *,
        draft_options: list[str],
        profile_summary: str,
        lang: str = "en",
    ) -> str:
        """Return Telegram HTML (not Markdown)."""
        client = LLMClient.from_settings(review=True)
        title = "Review" if lang != "ru" else "Ревью"
        bullets = "\n".join(f"- {o[:120]}" for o in draft_options[:3])
        if lang == "ru":
            system = (
                "Дай 2–3 коротких замечания к черновикам. JSON: points[{label, note}]. "
                "label ≤ 6 слов, note ≤ 20 слов. Без markdown, без нумерации 1.2.3."
            )
        else:
            system = (
                "Give 2–3 short notes on the drafts. JSON: points[{label, note}]. "
                "label ≤ 6 words, note ≤ 20 words. No markdown, no numbered lists."
            )
        raw = await client.chat(
            [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"Profile:\n{profile_summary[:1500]}\n\nDrafts:\n{bullets}",
                },
            ],
            response_format=REVIEW_RESPONSE_FORMAT,
        )
        points = parse_review_points(raw)
        return format_review_message(title=title, points=points)
