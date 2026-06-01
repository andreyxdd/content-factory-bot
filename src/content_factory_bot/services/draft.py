"""Writing step — structured JSON drafts (Karpathy-style: one call, no agent harness)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

from content_factory_bot.llm.client import LLMClient
from content_factory_bot.services.prompt_guard import wrap_user_content
from content_factory_bot.services.style_length import char_range_for_band, length_band_from_style_card

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
        self.last_system_message = ""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        for m in messages:
            if m.get("role") == "system":
                self.last_system_message = m.get("content", "")
            if m.get("role") == "user":
                self.last_user_message = m.get("content", "")
        return self._body


ANGLES_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "angle_round",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "angles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "format": {"type": "string"},
                            "hook": {"type": "string"},
                            "preview": {"type": "string"},
                        },
                        "required": ["id", "format", "hook", "preview"],
                        "additionalProperties": False,
                    },
                    "minItems": 3,
                    "maxItems": 3,
                }
            },
            "required": ["angles"],
            "additionalProperties": False,
        },
    },
}

ENDINGS_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "ending_ab",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "question_ending": {"type": "string"},
                "punch_ending": {"type": "string"},
            },
            "required": ["question_ending", "punch_ending"],
            "additionalProperties": False,
        },
    },
}


@dataclass(frozen=True)
class AngleOption:
    id: str
    format: str
    hook: str
    preview: str

    def display_block(self, lang: str) -> str:
        fmt_label = self.format
        sep = "─" * 41
        if lang == "ru":
            return (
                f"УГОЛ {self.id} — {fmt_label}\n"
                f"{sep}\n"
                f"HOOK: {self.hook}\n\n"
                f"{self.preview}"
            )
        return (
            f"ANGLE {self.id} — {fmt_label}\n"
            f"{sep}\n"
            f"HOOK: {self.hook}\n\n"
            f"{self.preview}"
        )


def _parse_angles(raw: str) -> list[AngleOption]:
    data = json.loads(raw)
    angles = data.get("angles")
    if not isinstance(angles, list) or len(angles) != 3:
        raise ValueError(f"Expected 3 angles, got: {angles!r}")
    out: list[AngleOption] = []
    for item in angles:
        out.append(
            AngleOption(
                id=str(item["id"]),
                format=str(item["format"]),
                hook=str(item["hook"]),
                preview=str(item["preview"]),
            )
        )
    return out


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

    def _messages(
        self,
        *,
        system_prompt: str,
        user_content: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

    async def generate_three_angles(
        self,
        *,
        system_prompt: str,
        style_card: str,
        content_language: str,
        input_text: str,
        research_brief: str | None = None,
    ) -> list[AngleOption]:
        task = (
            "Generate exactly 3 angles on the creator's idea. "
            "Each angle uses a DIFFERENT format from: story, conflict, practice, reflection. "
            "Each angle uses a DIFFERENT hook type. "
            f"Write in locale '{content_language}'."
        )
        parts = [
            f"<style_card>\n{style_card}\n</style_card>",
            wrap_user_content("idea", input_text),
        ]
        if research_brief:
            parts.append(f"<research>\n{research_brief}\n</research>")
        user = "\n\n".join(parts) + "\n\n" + task
        raw = await self._client_or_default().chat(
            self._messages(system_prompt=system_prompt, user_content=user),
            response_format=ANGLES_RESPONSE_FORMAT,
        )
        return _parse_angles(raw)

    async def edit_selected_angle(
        self,
        *,
        system_prompt: str,
        style_card: str,
        content_language: str,
        input_text: str,
        angle: AngleOption,
        edit_instruction: str,
    ) -> AngleOption:
        user = (
            f"<style_card>\n{style_card}\n</style_card>\n"
            f"{wrap_user_content('idea', input_text)}\n"
            f'<selected_angle id="{angle.id}" format="{angle.format}">\n'
            f"HOOK: {angle.hook}\n{angle.preview}\n"
            f"</selected_angle>\n"
            f"{wrap_user_content('edit_instruction', edit_instruction)}\n"
            "Revise ONLY this angle hook and preview. "
            f"Locale: {content_language}. Return JSON angles array length 3."
        )
        raw = await self._client_or_default().chat(
            self._messages(system_prompt=system_prompt, user_content=user),
            response_format=ANGLES_RESPONSE_FORMAT,
        )
        angles = _parse_angles(raw)
        for a in angles:
            if a.id == angle.id:
                return a
        return angles[0]

    async def expand_selected_angle_to_full_post(
        self,
        *,
        system_prompt: str,
        style_card: str,
        content_language: str,
        input_text: str,
        angle: AngleOption,
    ) -> str:
        band = length_band_from_style_card(style_card)
        lo, hi = char_range_for_band(band)
        user = (
            f"<style_card>\n{style_card}\n</style_card>\n"
            f"Target length band: {band} ({lo}-{hi} characters).\n"
            f"{wrap_user_content('idea', input_text)}\n"
            f'<selected_angle id="{angle.id}" format="{angle.format}">\n'
            f"HOOK: {angle.hook}\n{angle.preview}\n"
            f"</selected_angle>\n"
            "Expand into a full post. Return ONLY the post body text."
            f" Locale: {content_language}."
        )
        return (
            await self._client_or_default().chat(
                self._messages(system_prompt=system_prompt, user_content=user)
            )
        ).strip()

    async def generate_two_endings(
        self,
        *,
        system_prompt: str,
        style_card: str,
        content_language: str,
        full_post: str,
    ) -> tuple[str, str]:
        user = (
            f"<style_card>\n{style_card}\n</style_card>\n"
            f"{wrap_user_content('full_post', full_post)}\n"
            "Return two alternative FINAL paragraphs only: "
            "question_ending (open question) and punch_ending (short punchy takeaway). "
            f"Locale: {content_language}."
        )
        raw = await self._client_or_default().chat(
            self._messages(system_prompt=system_prompt, user_content=user),
            response_format=ENDINGS_RESPONSE_FORMAT,
        )
        data = json.loads(raw)
        return str(data["question_ending"]), str(data["punch_ending"])

    async def rewrite_post_with_feedback(
        self,
        *,
        system_prompt: str,
        style_card: str,
        content_language: str,
        full_post: str,
        feedback: str,
    ) -> str:
        user = (
            f"<style_card>\n{style_card}\n</style_card>\n"
            f"{wrap_user_content('full_post', full_post)}\n"
            f"{wrap_user_content('feedback', feedback)}\n"
            "Rewrite the full post incorporating feedback. Return ONLY post text."
            f" Locale: {content_language}."
        )
        return (
            await self._client_or_default().chat(
                self._messages(system_prompt=system_prompt, user_content=user)
            )
        ).strip()

    async def replace_final_paragraph(
        self,
        *,
        full_post: str,
        new_paragraph: str,
    ) -> str:
        parts = full_post.rstrip().split("\n\n")
        if not parts:
            return new_paragraph.strip()
        parts[-1] = new_paragraph.strip()
        return "\n\n".join(parts)
