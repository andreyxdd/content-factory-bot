import re

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
    prompt = build_system_prompt(answers, "STYLE", values, tribal, "en")
    assert "I am a creator" in prompt
    assert "STYLE" in prompt
    assert "FINAL CHECK BEFORE OUTPUT" in prompt


def test_en_style_card_has_no_cyrillic_antimarkers() -> None:
    text = build_style_card(["I ship fast and iterate weekly."], "en")
    assert re.search(r"[А-Яа-яЁё]", text) is None
    assert "important to note" in text or "in conclusion" in text


def test_ru_style_card_and_prompt_have_no_english_template_headers() -> None:
    style = build_style_card(["Я пишу коротко и без воды."], "ru")
    assert "Person:" not in style
    assert "Self-disclosure" not in style
    assert "important to note" not in style
    prompt = build_system_prompt(
        {"s2_about": "Я автор", "s2_audience": "Фаундеры", "s2_platforms": "Телеграм"},
        style,
        build_values_block({"s4_beliefs": "Простота лучше шума"}, "ru"),
        build_tribal_block({"s5_reader_phrase": "Это про меня"}, "ru"),
        "ru",
    )
    assert "# КТО Я" in prompt
    assert "# WHO I AM" not in prompt
