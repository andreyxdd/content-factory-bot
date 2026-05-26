from pathlib import Path

import yaml

from content_factory_bot.onboarding.loader import load_questions

CHOICE_ONLY_KEYS = frozenset({"primary_language", "web_research", "review_agent"})


def test_onboarding_question_bank() -> None:
    path = Path(__file__).resolve().parents[1] / "src/content_factory_bot/onboarding/questions.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 14
    keys = [q["key"] for q in data]
    assert keys == [
        "primary_language",
        "occupation",
        "content_goals",
        "audience",
        "voice_tone",
        "formats",
        "niche_topics",
        "hard_limits",
        "signature_themes",
        "personal_angle",
        "human_design",
        "cadence",
        "web_research",
        "review_agent",
    ]
    for q in load_questions():
        en_len = len(q.options["en"])
        ru_len = len(q.options["ru"])
        assert en_len == ru_len, q.key
        assert q.recommended < en_len, q.key
        assert q.choice_only == (q.key in CHOICE_ONLY_KEYS), q.key
