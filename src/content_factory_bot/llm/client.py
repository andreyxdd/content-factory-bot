"""Thin OpenAI-compatible client. Orchestrator lives in services/ (Phase 2)."""

from typing import Any

import httpx

from content_factory_bot.config import get_settings
from content_factory_bot.llm.parse import message_content_from_response


class LLMClient:
    """HTTP chat completions — not an agent harness."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @classmethod
    def from_settings(
        cls,
        *,
        fast: bool = False,
        research: bool = False,
        review: bool = False,
    ) -> "LLMClient":
        settings = get_settings()
        api_key = getattr(settings, "openrouter_api_key", None) or ""
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")
        if research:
            model = settings.llm_model_research
        elif review:
            model = settings.llm_model_review
        elif fast:
            model = settings.llm_model_fast
        else:
            model = settings.llm_model_draft
        return cls(
            api_key=api_key,
            base_url=settings.llm_base_url,
            model=model,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
        return message_content_from_response(data)
