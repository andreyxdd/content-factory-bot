from content_factory_bot.locale.i18n import t
from content_factory_bot.onboarding.loader import Question


def format_question_body(q: Question, lang: str) -> str:
    lines = [f"<b>{q.prompt(lang)}</b>", ""]
    opts = q.options.get(lang) or q.options["en"]
    for i, label in enumerate(opts[:3]):
        star = "⭐ " if i == q.recommended else ""
        lines.append(f"{i + 1}. {star}{label}")
    lines.append("")
    lines.append(t("onboarding_pick_or_type", lang))
    return "\n".join(lines)


def parse_text_answer(
    q: Question,
    lang: str,
    text: str,
) -> tuple[str, int | None, bool] | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped in ("1", "2", "3"):
        idx = int(stripped) - 1
        return q.option_label(lang, idx), idx, False
    return stripped, None, True
