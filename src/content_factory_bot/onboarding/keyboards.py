from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from content_factory_bot.onboarding.loader import Question


def question_keyboard(q: Question, lang: str, *, prefix: str = "ob") -> InlineKeyboardMarkup:
    opts = q.options.get(lang) or q.options["en"]
    rec = q.recommended
    rows: list[list[InlineKeyboardButton]] = []
    pair: list[InlineKeyboardButton] = []
    for i, label in enumerate(opts[:3]):
        text = f"⭐ {label}" if i == rec else label
        pair.append(
            InlineKeyboardButton(
                text=text[:64],
                callback_data=f"{prefix}:{q.key}:{i}",
            )
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    custom = "✏️ " + ("Свой ответ" if lang == "ru" else "Custom reply")
    rows.append([InlineKeyboardButton(text=custom, callback_data=f"{prefix}:{q.key}:custom")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
