from content_factory_bot.locale.i18n import t
from content_factory_bot.onboarding.format import format_question_body, parse_text_answer
from content_factory_bot.onboarding.keyboards import question_keyboard
from content_factory_bot.onboarding.loader import load_questions


def test_format_question_body_lists_options_with_star_on_recommended() -> None:
    q = next(x for x in load_questions() if x.key == "occupation")
    body = format_question_body(q, "en")
    assert "<b>What best describes what you do?</b>" in body
    assert "⭐ Founder / builder" in body
    assert "2. Expert / practitioner" in body
    assert "3. Creator / media personality" in body
    assert "Suggested:" not in body
    assert t("onboarding_pick_or_type", "en") in body


def test_question_keyboard_has_three_numeric_buttons_only() -> None:
    q = next(x for x in load_questions() if x.key == "occupation")
    kb = question_keyboard(q, "en")
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    assert len(buttons) == 3
    assert len(kb.inline_keyboard) == 3
    assert all(len(row) == 1 for row in kb.inline_keyboard)
    assert [b.text for b in buttons] == ["1", "2", "3"]
    assert all("custom" not in b.callback_data for b in buttons)
    assert buttons[0].callback_data == "ob:occupation:0"


def test_parse_text_answer_maps_digits_to_options() -> None:
    q = next(x for x in load_questions() if x.key == "occupation")
    label, idx, is_custom = parse_text_answer(q, "en", " 2 ")
    assert label == q.option_label("en", 1)
    assert idx == 1
    assert is_custom is False


def test_parse_text_answer_custom_verbatim() -> None:
    q = next(x for x in load_questions() if x.key == "occupation")
    label, idx, is_custom = parse_text_answer(q, "en", "Independent consultant")
    assert label == "Independent consultant"
    assert idx is None
    assert is_custom is True


def test_parse_text_answer_ignores_whitespace() -> None:
    q = next(x for x in load_questions() if x.key == "occupation")
    assert parse_text_answer(q, "en", "   ") is None
