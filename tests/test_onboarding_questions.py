from pathlib import Path

import yaml


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
