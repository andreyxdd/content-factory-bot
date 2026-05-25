import pytest

from content_factory_bot.services.stt import StubSTT, transcribe_audio


@pytest.mark.asyncio
async def test_stub_stt_returns_transcript() -> None:
    text = await transcribe_audio(b"fake", client=StubSTT("Hello from voice"))
    assert text == "Hello from voice"
