import json
from unittest.mock import patch

import pytest

from content_factory_bot.locale.telegram_html import (
    format_review_message,
    markdown_bold_to_html,
    parse_review_points,
)
from content_factory_bot.services.draft import StubChatClient
from content_factory_bot.services.review import ReviewStep


def test_format_review_message_uses_html_bullets() -> None:
    html = format_review_message(
        title="Review",
        points=[("Hook", "Sharpen the opener"), ("Tone", "More relief")],
    )
    assert html.startswith("<b>Review</b>")
    assert "• <b>Hook</b> — Sharpen" in html
    assert "**" not in html


def test_markdown_bold_converted() -> None:
    assert markdown_bold_to_html("**A:** text") == "<b>A:</b> text"


def test_parse_review_points_json() -> None:
    raw = json.dumps(
        {
            "points": [
                {"label": "Clarity", "note": "Drop duplicate opener"},
                {"label": "Tone", "note": "Add reassurance"},
            ]
        }
    )
    pts = parse_review_points(raw)
    assert len(pts) == 2
    assert pts[0][0] == "Clarity"


@pytest.mark.asyncio
async def test_critique_returns_telegram_html() -> None:
    stub = StubChatClient(
        json.dumps(
            {
                "points": [
                    {"label": "Focus", "note": "One clear hook"},
                    {"label": "Depth", "note": "Add one example"},
                ]
            }
        )
    )

    with patch(
        "content_factory_bot.services.review.LLMClient.from_settings",
        return_value=stub,
    ):
        html = await ReviewStep().critique(
            draft_options=["draft a", "draft b"],
            profile_summary="Tone: direct",
            lang="en",
        )

    assert "<b>Review</b>" in html
    assert "<b>Focus</b>" in html
    assert "**" not in html
    assert len(html) < 600
