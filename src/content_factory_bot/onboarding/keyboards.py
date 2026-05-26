from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from content_factory_bot.onboarding.loader import Question


def question_keyboard(q: Question, lang: str, *, prefix: str = "ob") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(q.option_count(lang)):
        rows.append(
            [
                InlineKeyboardButton(
                    text=str(i + 1),
                    callback_data=f"{prefix}:{q.key}:{i}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
