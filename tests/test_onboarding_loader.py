from content_factory_bot.onboarding.loader import load_questions


def test_load_questions_returns_fourteen() -> None:
    questions = load_questions()
    assert len(questions) == 14
    assert questions[0].key == "primary_language"
    assert questions[-1].key == "review_agent"


def test_occupation_question_prompt() -> None:
    q = load_questions()[1]
    assert q.key == "occupation"
    assert "do" in q.prompt("en").lower() or "занимаетесь" in q.prompt("ru").lower()
