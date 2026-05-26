from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_QUESTIONS_PATH = Path(__file__).parent / "questions.yaml"


@dataclass(frozen=True)
class Question:
    key: str
    prompts: dict[str, str]
    recommended: int
    options: dict[str, list[str]]

    def prompt(self, lang: str) -> str:
        return self.prompts.get(lang) or self.prompts["en"]

    def options_for(self, lang: str) -> list[str]:
        return list(self.options.get(lang) or self.options["en"])

    def option_count(self, lang: str) -> int:
        return len(self.options_for(lang))

    @property
    def choice_only(self) -> bool:
        counts = {len(opts) for opts in self.options.values()}
        return counts == {2}

    def option_label(self, lang: str, index: int) -> str:
        return self.options_for(lang)[index]

    def recommended_label(self, lang: str) -> str:
        return self.option_label(lang, self.recommended)


@lru_cache
def load_questions() -> tuple[Question, ...]:
    raw = yaml.safe_load(_QUESTIONS_PATH.read_text(encoding="utf-8"))
    return tuple(
        Question(
            key=item["key"],
            prompts=item["prompts"],
            recommended=item["recommended"],
            options=item["options"],
        )
        for item in raw
    )


def get_question(key: str) -> Question | None:
    return next((q for q in load_questions() if q.key == key), None)


def next_unanswered(answered_keys: set[str]) -> Question | None:
    for q in load_questions():
        if q.key not in answered_keys:
            return q
    return None
