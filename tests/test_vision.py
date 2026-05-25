import pytest

from content_factory_bot.services.vision import StubVision, describe_image


@pytest.mark.asyncio
async def test_stub_vision_returns_description() -> None:
    text = await describe_image(b"fake", client=StubVision("A desk with a laptop"))
    assert "laptop" in text
