from content_factory_bot.services.onboarding_engine import (
    build_s2_summary,
    build_style_card,
    build_system_prompt,
    build_tribal_block,
    build_values_block,
)


def test_build_s2_summary_contains_expected_fields() -> None:
    text = build_s2_summary(
        {
            "s2_about": "I coach founders",
            "s2_audience": "B2B SaaS founders 30-45",
            "s2_platforms": "Telegram, LinkedIn",
            "s2_goals": "a,c",
            "s2_reader_feel": "I am not alone",
            "s2_avoid_topics": "politics",
        },
        "en",
    )
    assert "I coach founders" in text
    assert "Telegram, LinkedIn" in text


def test_build_style_card_empty_samples_safe() -> None:
    text = build_style_card([], "ru")
    assert "образцов" in text


def test_build_system_prompt_includes_tribal_and_values() -> None:
    answers = {"s2_about": "I am a creator", "s2_audience": "Founders", "s2_platforms": "Telegram"}
    values = build_values_block({"s4_beliefs": "Slow is smooth"}, "en")
    tribal = build_tribal_block({"s5_reader_phrase": "I should try this"}, "en")
    prompt = build_system_prompt(answers, "STYLE", values, tribal)
    assert "I am a creator" in prompt
    assert "STYLE" in prompt
    assert "TRIBAL CHECK" in prompt
