from content_factory_bot.handlers.onboarding import _question_text


def test_toggle_warning_present_in_both_locales() -> None:
    ru = _question_text("toggle_warning", "ru").lower()
    en = _question_text("toggle_warning", "en").lower()
    assert "токен" in ru
    assert "token" in en
    assert "web_research" in en
    assert "review_agent" in en
