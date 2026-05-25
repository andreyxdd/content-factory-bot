from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def draft_options_keyboard(
    session_id: int,
    round_no: int,
    options: list[str],
    lang: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    pair: list[InlineKeyboardButton] = []
    for i, label in enumerate(options[:3]):
        text = (label[:60] + "…") if len(label) > 60 else label
        pair.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"cs:{session_id}:pick:{round_no}:{i}",
            )
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    custom = "✏️ " + ("Свой ответ" if lang == "ru" else "Custom reply")
    rows.append(
        [
            InlineKeyboardButton(
                text=custom,
                callback_data=f"cs:{session_id}:custom:{round_no}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def follow_up_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        new_l, edit_l, ok_l = "Три новых", "Править выбранный", "Подтвердить"
    else:
        new_l, edit_l, ok_l = "Three new", "Edit selected", "Confirm draft"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=new_l, callback_data=f"cs:{session_id}:fu:new"
                ),
                InlineKeyboardButton(
                    text=edit_l, callback_data=f"cs:{session_id}:fu:refine"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ok_l, callback_data=f"cs:{session_id}:fu:confirm"
                )
            ],
        ]
    )


def publish_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    label = "Опубликовать" if lang == "ru" else "Publish now"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"cs:{session_id}:publish"
                )
            ]
        ]
    )


def sessions_list_keyboard(
    sessions: list[tuple[int, str, str]], lang: str
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for sid, title, state in sessions:
        label = f"{title[:40]} ({state})"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"cs:resume:{sid}"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows or [[]])
