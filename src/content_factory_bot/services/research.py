"""Research step — Sonar-style brief after session input (stub LLM when no API)."""

import logging
from typing import Any, Protocol

from content_factory_bot.llm.client import LLMClient

logger = logging.getLogger(__name__)


class ChatClient(Protocol):
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str: ...


class ResearchStep:
    def __init__(self, client: ChatClient | None = None) -> None:
        self._client = client

    def _client_or_default(self) -> ChatClient:
        if self._client is not None:
            return self._client
        try:
            return LLMClient.from_settings(research=True)
        except ValueError:
            logger.warning("OPENROUTER_API_KEY missing — offline research stub")

            class _BriefStub:
                async def chat(self, messages, *, response_format=None) -> str:
                    return (
                        "Offline research stub: emphasize the Creator's angle "
                        "and one timely hook tied to their input."
                    )

            return _BriefStub()  # type: ignore[return-value]

    async def run(self, *, profile_summary: str, input_text: str) -> str:
        system = (
            "Summarize timely angles, hooks, and facts for this post idea. "
            "Short bullet brief, plain text, under 400 words."
        )
        user = f"Profile:\n{profile_summary}\n\nPost idea:\n{input_text}"
        return await self._client_or_default().chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
