"""Writing step — structured JSON drafts (Karpathy-style: one call, no agent harness)."""

import json
import logging
from typing import Any, Protocol

from content_factory_bot.llm.client import LLMClient

logger = logging.getLogger(__name__)

DRAFT_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "draft_round",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
            "required": ["options"],
            "additionalProperties": False,
        },
    },
}


class ChatClient(Protocol):
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str: ...


class StubChatClient:
    """Test double — records last user message."""

    def __init__(self, response_body: str) -> None:
        self._body = response_body
        self.last_user_message = ""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                self.last_user_message = m.get("content", "")
                break
        return self._body


def _parse_options(raw: str) -> list[str]:
    data = json.loads(raw)
    options = data.get("options")
    if not isinstance(options, list) or len(options) != 3:
        raise ValueError(f"Expected 3 options, got: {options!r}")
    return [str(o) for o in options]


class DraftOrchestrator:
    def __init__(self, client: ChatClient | None = None) -> None:
        self._client = client

    def _client_or_default(self) -> ChatClient:
        if self._client is not None:
            return self._client
        try:
            return LLMClient.from_settings()
        except ValueError:
            logger.warning("OPENROUTER_API_KEY missing — offline draft stub")
            return StubChatClient(
                json.dumps(
                    {
                        "options": [
                            "Draft option 1",
                            "Draft option 2",
                            "Draft option 3",
                        ]
                    }
                )
            )

    async def generate_initial_round(
        self,
        *,
        profile_summary: str,
        content_language: str = "en",
        input_text: str,
        research_brief: str | None = None,
    ) -> list[str]:
        system = (
            "You are a personal content writer. Return JSON with exactly three "
            "distinct draft options for the Creator's post. Match their profile tone. "
            f"Write in language locale '{content_language}'."
        )
        parts = [
            f"<profile>\n{profile_summary}\n</profile>",
            f"<brief>\n{input_text}\n</brief>",
        ]
        if research_brief:
            parts.append(f"<research>\n{research_brief}\n</research>")
        user = "\n\n".join(parts)
        raw = await self._client_or_default().chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=DRAFT_RESPONSE_FORMAT,
        )
        return _parse_options(raw)

    async def generate_follow_up_round(
        self,
        *,
        profile_summary: str,
        content_language: str = "en",
        input_text: str,
        prior_options: list[str],
        selected_index: int,
        feedback: str | None,
    ) -> list[str]:
        system = (
            "Generate three NEW draft options (not repeats). JSON schema with "
            f"options array of length 3. Write in language locale '{content_language}'."
        )
        selected = prior_options[selected_index]
        user = (
            f"<profile>\n{profile_summary}\n</profile>\n"
            f"<brief>\n{input_text}\n</brief>\n"
            f"<selected_draft>\n{selected}\n</selected_draft>\n"
        )
        if feedback:
            user += f"<feedback>\n{feedback}\n</feedback>\n"
        raw = await self._client_or_default().chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=DRAFT_RESPONSE_FORMAT,
        )
        return _parse_options(raw)

    async def refine_selected(
        self,
        *,
        profile_summary: str,
        content_language: str = "en",
        input_text: str,
        selected_text: str,
        feedback: str | None,
    ) -> list[str]:
        """Refinement: 1 edited + 2 new (returned as 3 options)."""
        system = (
            "Refine the selected draft and add two alternative angles. "
            "Return JSON with exactly three options; first should be the refined main draft. "
            f"Write in language locale '{content_language}'."
        )
        user = (
            f"<profile>\n{profile_summary}\n</profile>\n"
            f"<brief>\n{input_text}\n</brief>\n"
            f"<selected>\n{selected_text}\n</selected>\n"
        )
        if feedback:
            user += f"<feedback>\n{feedback}\n</feedback>\n"
        raw = await self._client_or_default().chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=DRAFT_RESPONSE_FORMAT,
        )
        return _parse_options(raw)
