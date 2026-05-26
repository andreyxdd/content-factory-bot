from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from content_factory_bot.onboarding.loader import Question


def question_keyboard(q: Question, lang: str, *, prefix: str = "ob") -> InlineKeyboardMarkup:
    del lang  # options shown in message body; keyboard is numeric only
    rows: list[list[InlineKeyboardButton]] = []
    pair: list[InlineKeyboardButton] = []
    for i in range(3):
        pair.append(
            InlineKeyboardButton(
                text=str(i + 1),
                callback_data=f"{prefix}:{q.key}:{i}",
            )
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    return InlineKeyboardMarkup(inline_keyboard=rows)
