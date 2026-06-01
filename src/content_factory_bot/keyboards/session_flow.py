from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from content_factory_bot.locale.i18n import t
def setup_keyboard(
    lang: str, *, research: bool, cover: bool, has_instructions: bool = False
) -> InlineKeyboardMarkup:
    r = "✅ " if research else ""
    c = "✅ " if cover else ""
    i = "✅ " if has_instructions else ""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"{r}{t('session_research', lang)}",
                callback_data="cs:toggle:research",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{c}{t('session_cover', lang)}",
                callback_data="cs:toggle:cover",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{i}{t('session_instructions', lang)}",
                callback_data="cs:setup:instructions",
            )
        ],
    ]
    if has_instructions:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("session_instructions_clear", lang),
                    callback_data="cs:setup:clear_instructions",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t("session_start", lang),
                callback_data="cs:start",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def angle_post_pick_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_edit_selected", lang),
                    callback_data=f"cs:{session_id}:angle:edit",
                ),
                InlineKeyboardButton(
                    text=t("session_expand_post", lang),
                    callback_data=f"cs:{session_id}:angle:expand",
                ),
            ],
        ]
    )


def angle_choice_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="A", callback_data=f"cs:{session_id}:angle:A"
                ),
                InlineKeyboardButton(
                    text="B", callback_data=f"cs:{session_id}:angle:B"
                ),
                InlineKeyboardButton(
                    text="C", callback_data=f"cs:{session_id}:angle:C"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("session_edit_selected", lang),
                    callback_data=f"cs:{session_id}:angle:edit",
                )
            ],
        ]
    )


def angle_edit_cap_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_expand_current", lang),
                    callback_data=f"cs:{session_id}:angle:expand",
                ),
                InlineKeyboardButton(
                    text=t("session_restart_angles", lang),
                    callback_data=f"cs:{session_id}:angle:restart",
                ),
            ],
        ]
    )


def ending_offer_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_ending_yes", lang),
                    callback_data=f"cs:{session_id}:ending:yes",
                ),
                InlineKeyboardButton(
                    text=t("session_ending_no", lang),
                    callback_data=f"cs:{session_id}:ending:no",
                ),
            ],
        ]
    )


def ending_pick_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_ending_question", lang),
                    callback_data=f"cs:{session_id}:ending:q",
                ),
                InlineKeyboardButton(
                    text=t("session_ending_punch", lang),
                    callback_data=f"cs:{session_id}:ending:p",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("session_ending_regen", lang),
                    callback_data=f"cs:{session_id}:ending:regen",
                ),
            ],
        ]
    )


def tribal_check_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_tribal_yes", lang),
                    callback_data=f"cs:{session_id}:tribal:yes",
                ),
                InlineKeyboardButton(
                    text=t("session_tribal_no", lang),
                    callback_data=f"cs:{session_id}:tribal:no",
                ),
            ],
        ]
    )


def finalize_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐ {t('session_save_later', lang)}",
                    callback_data=f"cs:{session_id}:fin:save",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("session_post_now", lang),
                    callback_data=f"cs:{session_id}:fin:post",
                ),
            ],
        ]
    )


def publish_scope_keyboard(session_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("session_publish_all", lang),
                    callback_data=f"cs:{session_id}:pub:all",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("session_publish_choose", lang),
                    callback_data=f"cs:{session_id}:pub:choose",
                ),
            ],
        ]
    )


def publish_dest_keyboard(
    session_id: int,
    lang: str,
    connected: list[str],
    selected: set[str],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for prov in connected:
        mark = "✅ " if prov in selected else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark}{prov}",
                    callback_data=f"cs:{session_id}:pubdest:{prov}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t("session_publish_confirm", lang),
                callback_data=f"cs:{session_id}:pub:go",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def partial_publish_retry_keyboard(
    session_id: int, lang: str, failed: list[str]
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"↻ {p}",
                callback_data=f"cs:{session_id}:pubretry:{p}",
            )
        ]
        for p in failed
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
