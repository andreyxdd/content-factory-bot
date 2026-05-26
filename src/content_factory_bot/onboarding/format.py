from content_factory_bot.locale.i18n import t
from content_factory_bot.onboarding.loader import Question


def format_question_body(q: Question, lang: str) -> str:
    lines = [f"<b>{q.prompt(lang)}</b>", ""]
    for i, label in enumerate(q.options_for(lang)):
        star = "⭐ " if i == q.recommended else ""
        lines.append(f"{i + 1}. {star}{label}")
    lines.append("")
    footer_key = "onboarding_pick_only" if q.choice_only else "onboarding_pick_or_type"
    lines.append(t(footer_key, lang))
    return "\n".join(lines)


def parse_text_answer(
    q: Question,
    lang: str,
    text: str,
) -> tuple[str, int | None, bool] | None:
    stripped = text.strip()
    if not stripped:
        return None
    valid_digits = tuple(str(i + 1) for i in range(q.option_count(lang)))
    if stripped in valid_digits:
        idx = int(stripped) - 1
        return q.option_label(lang, idx), idx, False
    if q.choice_only:
        return None
    return stripped, None, True
