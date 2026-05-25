"""Speech-to-text — OpenAI-compatible audio API or stub."""

import logging
from typing import Protocol

import httpx

from content_factory_bot.config import get_settings

logger = logging.getLogger(__name__)


class STTClient(Protocol):
    async def transcribe(self, audio_bytes: bytes, *, mime: str = "audio/ogg") -> str: ...


class StubSTT:
    def __init__(self, text: str) -> None:
        self._text = text

    async def transcribe(self, audio_bytes: bytes, *, mime: str = "audio/ogg") -> str:
        return self._text


class WhisperSTT:
    def __init__(self, *, api_key: str, base_url: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def transcribe(self, audio_bytes: bytes, *, mime: str = "audio/ogg") -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{self._base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": ("audio.ogg", audio_bytes, mime)},
                data={"model": "whisper-1"},
            )
            r.raise_for_status()
            return r.json()["text"]


def _client_or_default(client: STTClient | None) -> STTClient:
    if client is not None:
        return client
    settings = get_settings()
    if settings.openrouter_api_key:
        return WhisperSTT(
            api_key=settings.openrouter_api_key,
            base_url=settings.llm_base_url.replace("/v1", "/v1"),
        )
    return StubSTT("[voice transcript unavailable — set OPENROUTER_API_KEY]")


async def transcribe_audio(
    audio_bytes: bytes,
    *,
    client: STTClient | None = None,
    mime: str = "audio/ogg",
) -> str:
    try:
        return await _client_or_default(client).transcribe(audio_bytes, mime=mime)
    except Exception:
        logger.exception("STT failed")
        return StubSTT("[voice transcription failed]")._text  # noqa: SLF001
