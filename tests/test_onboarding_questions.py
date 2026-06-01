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


def test_scripted_questions_are_verbatim_in_english() -> None:
    assert _question_text("s2_goals", "en") == (
        "Why do you need content? Pick what fits most (multiple allowed):\n"
        "(a) sell product/service\n"
        "(b) build community\n"
        "(c) build personal brand / authority\n"
        "(d) find partners and network\n"
        "(e) other - describe"
    )
    assert _question_text("s4_beliefs", "en") == (
        "Name 2-3 beliefs in your field that you think are right,\n"
        "while most of the industry disagrees. Something controversial, uncomfortable,\n"
        "against mainstream. These are your anchor points."
    )
    assert _question_text("s4_contradictions", "en") == (
        "What internal contradictions do you have that you sometimes\n"
        "say out loud? Example: ‘I say rest matters, but I\n"
        "work 12 hours.’ Contradictions are depth, not weakness."
    )
    assert _question_text("s4_intro", "en") == (
        "Style is half the voice. The other half is what’s in your head.\n"
        "Without this, AI can sound stylistically like you,\n"
        "but miss your substance. 4 quick questions."
    )


def test_scripted_questions_are_verbatim_in_russian() -> None:
    assert _question_text("s2_goals", "ru") == (
        "Зачем тебе контент? Выбери ближайшее (можно несколько):\n"
        "(a) продавать продукт/услугу\n"
        "(b) собирать комьюнити\n"
        "(c) строить личный бренд / экспертизу\n"
        "(d) находить партнёров и нетворк\n"
        "(e) другое - опиши"
    )
    assert _question_text("s4_beliefs", "ru") == (
        "Назови 2-3 убеждения в твоей сфере, которые ты считаешь правильными,\n"
        "а большинство в индустрии - нет. Что-то спорное, неудобное, против\n"
        "мейнстрима. Это твои опорные точки."
    )
    assert _question_text("s4_contradictions", "ru") == (
        "Какие у тебя есть внутренние противоречия, которые ты иногда\n"
        "проговариваешь вслух? Например: 'Я говорю что отдых важен, а сам\n"
        "работаю по 12 часов.' Противоречия - это глубина, не слабость."
    )
    assert _question_text("s4_intro", "ru") == (
        "Стиль - это половина голоса. Вторая половина - что у тебя\n"
        "в голове. Без этого AI будет писать стилистически похоже на тебя,\n"
        "но содержательно мимо. 4 быстрых вопроса."
    )
