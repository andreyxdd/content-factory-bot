import json

import pytest

from content_factory_bot.llm.parse import loads_json_object, message_content_from_response


def test_message_content_from_response_plain() -> None:
    data = {"choices": [{"message": {"content": "hello"}}]}
    assert message_content_from_response(data) == "hello"


def test_message_content_from_response_reasoning_fallback() -> None:
    data = {
        "choices": [
            {"message": {"content": "", "reasoning": '{"angles":[]}'}}
        ]
    }
    assert message_content_from_response(data) == '{"angles":[]}'


def test_message_content_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        message_content_from_response({"choices": [{"message": {"content": ""}}]})


def test_extract_json_text_strips_fence() -> None:
    raw = '```json\n{"angles": []}\n```'
    assert loads_json_object(raw) == {"angles": []}


@pytest.mark.asyncio
async def test_generate_three_angles_retries_on_bad_json() -> None:
    from content_factory_bot.services.draft import DraftOrchestrator

    calls: list[dict] = []

    class FlakyClient:
        async def chat(self, messages, *, response_format=None) -> str:
            calls.append({"format": response_format})
            if len(calls) == 1:
                return ""
            return json.dumps(
                {
                    "angles": [
                        {"id": "A", "format": "story", "hook": "h", "preview": "p"},
                        {"id": "B", "format": "conflict", "hook": "h", "preview": "p"},
                        {"id": "C", "format": "practice", "hook": "h", "preview": "p"},
                    ]
                }
            )

    angles = await DraftOrchestrator(client=FlakyClient()).generate_three_angles(
        system_prompt="SYS",
        style_card="short",
        content_language="en",
        input_text="idea",
    )
    assert len(angles) == 3
    assert len(calls) == 2
