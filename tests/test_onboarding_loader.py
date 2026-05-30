from content_factory_bot.services.onboarding_engine import ordered_profile_keys, required_answer_keys


def test_required_answers_include_toggles() -> None:
    required = required_answer_keys()
    assert "s2_about" in required
    assert "s2_audience" in required
    assert "s2_reader_feel" in required
    assert "s2_avoid_topics" in required
    assert "s5_voice_betrayal" in required
    assert "web_research" not in required
    assert "review_agent" not in required


def test_ordered_profile_keys_stable() -> None:
    keys = ordered_profile_keys()
    assert keys[0] == "s2_about"
    assert keys[-1] == "review_agent"
