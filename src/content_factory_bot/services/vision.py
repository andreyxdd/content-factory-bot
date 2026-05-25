"""Image context — vision LLM message or stub."""

import base64
import logging
from typing import Protocol

from content_factory_bot.llm.client import LLMClient

logger = logging.getLogger(__name__)


class VisionClient(Protocol):
    async def describe(self, image_bytes: bytes, *, mime: str = "image/jpeg") -> str: ...


class StubVision:
    def __init__(self, text: str) -> None:
        self._text = text

    async def describe(self, image_bytes: bytes, *, mime: str = "image/jpeg") -> str:
        return self._text


class LLMVision:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient.from_settings(fast=True)

    async def describe(self, image_bytes: bytes, *, mime: str = "image/jpeg") -> str:
        b64 = base64.standard_b64encode(image_bytes).decode()
        data_url = f"data:{mime};base64,{b64}"
        return await self._llm.chat(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image briefly for a content creator's post context.",
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ]
        )


def _client_or_default(client: VisionClient | None) -> VisionClient:
    if client is not None:
        return client
    try:
        return LLMVision()
    except ValueError:
        return StubVision("[image description unavailable — set OPENROUTER_API_KEY]")


async def describe_image(
    image_bytes: bytes,
    *,
    client: VisionClient | None = None,
    mime: str = "image/jpeg",
) -> str:
    try:
        return await _client_or_default(client).describe(image_bytes, mime=mime)
    except Exception:
        logger.exception("vision failed")
        return "[image description failed]"
