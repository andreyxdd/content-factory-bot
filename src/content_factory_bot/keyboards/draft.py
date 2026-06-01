from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def draft_options_keyboard(
    session_id: int,
    round_no: int,
    options: list[str],
    lang: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i, label in enumerate(options[:3]):
        text = (label[:60] + "…") if len(label) > 60 else label
        rows.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"cs:{session_id}:pick:{round_no}:{i}",
                )
            ]
        )
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
    from content_factory_bot.locale.i18n import t

    rows: list[list[InlineKeyboardButton]] = []
    delete_label = t("session_delete_btn", lang)
    for sid, title, state in sessions:
        label = f"{title[:36]} ({state})"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"cs:resume:{sid}"
                ),
                InlineKeyboardButton(
                    text=delete_label, callback_data=f"cs:del:{sid}"
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows or [[]])


def session_delete_confirm_keyboard(sid: int, lang: str) -> InlineKeyboardMarkup:
    from content_factory_bot.locale.i18n import t

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_delete_yes", lang),
                    callback_data=f"cs:delok:{sid}",
                ),
                InlineKeyboardButton(
                    text=t("session_delete_no", lang),
                    callback_data=f"cs:dellist",
                ),
            ]
        ]
    )
