"""Parse LLM HTTP responses and JSON payloads."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def message_content_from_response(data: dict[str, Any]) -> str:
    """Extract text from OpenAI-compatible chat completion JSON."""
    choices = data.get("choices")
    if not choices:
        raise ValueError(f"LLM response missing choices: {data!r}")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text", "")))
        content = "\n".join(parts)
    text = str(content or "").strip()
    if text:
        return text
    for key in ("reasoning", "refusal"):
        alt = message.get(key)
        if isinstance(alt, str) and alt.strip():
            logger.info("LLM content empty; using message.%s", key)
            return alt.strip()
    raise ValueError(f"LLM returned empty message content: {message!r}")


def extract_json_text(raw: str) -> str:
    """Strip markdown fences and isolate JSON object from model text."""
    text = raw.strip()
    if not text:
        raise json.JSONDecodeError("empty LLM body", raw, 0)
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def loads_json_object(raw: str) -> dict[str, Any]:
    return json.loads(extract_json_text(raw))
