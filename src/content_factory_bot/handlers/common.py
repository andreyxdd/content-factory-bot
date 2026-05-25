from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.creators import ensure_creator

router = Router(name="common")


def _lang(message: Message, data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


@router.message(Command("start"))
async def cmd_start(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = _lang(message, data)
    uid = message.from_user.id

    async with session_scope() as session:
        await ensure_creator(
            session,
            telegram_user_id=uid,
            language_code=message.from_user.language_code,
        )

    detected = (
        t("locale_detected_ru", lang) if lang == "ru" else t("locale_detected_en", lang)
    )
    await message.answer(
        f"{t('welcome', lang)}\n\n{detected}\n\n{t('start_body', lang)}"
    )


@router.message(Command("help"))
async def cmd_help(message: Message, **data) -> None:
    await message.answer(t("help", _lang(message, data)))


@router.message(Command("new"))
async def cmd_new(message: Message, **data) -> None:
    await message.answer(t("new_pending", _lang(message, data)))


@router.message(Command("sessions"))
async def cmd_sessions(message: Message, **data) -> None:
    await message.answer(t("sessions_pending", _lang(message, data)))


@router.message(Command("onboarding"))
async def cmd_onboarding(message: Message, **data) -> None:
    await message.answer(t("onboarding_pending", _lang(message, data)))


@router.message(Command("profile"))
async def cmd_profile(message: Message, **data) -> None:
    await message.answer(t("profile_pending", _lang(message, data)))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, **data) -> None:
    await message.answer(t("cancel_idle", _lang(message, data)))
