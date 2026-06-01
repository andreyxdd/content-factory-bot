"""Build Telegram-safe HTML snippets (bot default parse_mode=HTML)."""

from __future__ import annotations

import html
import json
import re


def escape_html(text: str) -> str:
    return html.escape(text, quote=False)


def markdown_bold_to_html(text: str) -> str:
    """Fallback when model returns **bold** instead of <b>."""
    out: list[str] = []
    last = 0
    for match in re.finditer(r"\*\*(.+?)\*\*", text, re.DOTALL):
        out.append(escape_html(text[last : match.start()]))
        out.append(f"<b>{escape_html(match.group(1))}</b>")
        last = match.end()
    out.append(escape_html(text[last:]))
    return "".join(out)


def format_review_message(*, title: str, points: list[tuple[str, str]]) -> str:
    """Render review as short bullet list (max 3 points)."""
    lines = [f"<b>{escape_html(title)}</b>"]
    for label, note in points[:3]:
        label_s = escape_html(label.strip()[:48])
        note_s = escape_html(note.strip()[:160])
        if not label_s:
            continue
        lines.append(f"• <b>{label_s}</b> — {note_s}" if note_s else f"• <b>{label_s}</b>")
    return "\n".join(lines)


def parse_review_points(raw: str) -> list[tuple[str, str]]:
    """Parse JSON review payload or fall back to a single note."""
    try:
        from content_factory_bot.llm.parse import loads_json_object

        data = loads_json_object(raw)
        items = data.get("points")
        if isinstance(items, list):
            out: list[tuple[str, str]] = []
            for item in items[:3]:
                if isinstance(item, dict):
                    out.append((str(item.get("label", "")), str(item.get("note", ""))))
            if out:
                return out
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    text = markdown_bold_to_html(raw.strip())
    if len(text) > 500:
        text = text[:497] + "…"
    return [("Note", text)] if text else []
