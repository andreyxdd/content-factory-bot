"""TDD: draft round returns exactly three options from profile + session input."""

import json

import pytest

from content_factory_bot.services.draft import DraftOrchestrator, StubChatClient


@pytest.mark.asyncio
async def test_generates_three_draft_options_from_profile_and_input() -> None:
    stub = StubChatClient(
        json.dumps({"options": ["Hook A", "Hook B", "Hook C"]})
    )
    orch = DraftOrchestrator(client=stub)
    options = await orch.generate_initial_round(
        profile_summary="Tone: witty. Audience: devs.",
        input_text="Post about Redis job queues",
        research_brief=None,
    )
    assert len(options) == 3
    assert options[0] == "Hook A"
    assert "profile" in stub.last_user_message.lower() or "witty" in stub.last_user_message
    assert "Redis" in stub.last_user_message


@pytest.mark.asyncio
async def test_includes_research_brief_when_provided() -> None:
    stub = StubChatClient(
        json.dumps({"options": ["One", "Two", "Three"]})
    )
    orch = DraftOrchestrator(client=stub)
    await orch.generate_initial_round(
        profile_summary="Niche: AI tools",
        input_text="Launch announcement",
        research_brief="Trend: agents are hot in May 2026",
    )
    assert "Trend: agents" in stub.last_user_message


@pytest.mark.asyncio
async def test_follow_up_round_requests_three_new_options() -> None:
    stub = StubChatClient(
        json.dumps({"options": ["N1", "N2", "N3"]})
    )
    orch = DraftOrchestrator(client=stub)
    options = await orch.generate_follow_up_round(
        profile_summary="Tone: direct",
        input_text="Original brief",
        prior_options=["Old 1", "Old 2", "Old 3"],
        selected_index=1,
        feedback=None,
    )
    assert options == ["N1", "N2", "N3"]
