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


def test_anti_markers_question_contains_default_phrase() -> None:
    en = _question_text("s2_anti_markers", "en").lower()
    assert "it is important to note" in en
    assert "in conclusion" in en

    ru = _question_text("s2_anti_markers", "ru").lower()
    assert "важно отметить" in ru
    assert "в заключение" in ru


def test_toggle_research_help_explains_live_web_brief() -> None:
    en = _help_text("toggle_research", "en").lower()
    ru = _help_text("toggle_research", "ru").lower()
    assert "live web" in en
    assert "brief" in en
    assert "живого веба" in ru
    assert "brief" in ru
