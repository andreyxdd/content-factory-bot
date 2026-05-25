"""Inline keyboards: 3 options + custom reply (fourth button)."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def three_plus_custom(
    options: tuple[str, str, str],
    *,
    prefix: str,
    custom_label: str = "✏️ Custom reply",
) -> InlineKeyboardMarkup:
    """Build 3-option + fourth custom callback keyboard.

    callback_data kept short; ``prefix`` namespaces handlers (e.g. ob:, cs:).
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=options[0][:64], callback_data=f"{prefix}:0"),
                InlineKeyboardButton(text=options[1][:64], callback_data=f"{prefix}:1"),
            ],
            [InlineKeyboardButton(text=options[2][:64], callback_data=f"{prefix}:2")],
            [InlineKeyboardButton(text=custom_label, callback_data=f"{prefix}:custom")],
        ]
    )
