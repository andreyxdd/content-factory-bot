from content_factory_bot.handlers.onboarding import _help_text, _question_text


def test_toggle_warning_present_in_both_locales() -> None:
    ru = _question_text("toggle_warning", "ru").lower()
    en = _question_text("toggle_warning", "en").lower()
    assert "токен" in ru
    assert "token" in en
    assert "web_research" in en
    assert "review_agent" in en


def test_help_text_for_contrarian_beliefs_present_in_both_locales() -> None:
    ru = _help_text("s4_beliefs", "ru").lower()
    en = _help_text("s4_beliefs", "en").lower()
    assert "большинство" in ru
    assert "microservices" in en
    assert "big headcount" in en
