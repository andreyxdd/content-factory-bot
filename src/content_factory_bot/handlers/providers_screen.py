"""Shared /providers UI (command, post-onboarding, reminders)."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.api.oauth_signing import build_start_url
from content_factory_bot.config import get_settings
from content_factory_bot.db.models import ProviderKind
from content_factory_bot.db.session import session_scope
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.providers import ACTIVE, get_connections_map


def _localized_status_lines(conns: dict, lang: str) -> list[str]:
    lines = []
    for prov in (ProviderKind.TELEGRAM, ProviderKind.INSTAGRAM, ProviderKind.LINKEDIN):
        c = conns.get(prov)
        if c and c.status == ACTIVE:
            status = t("providers_status_connected", lang)
            if prov == ProviderKind.TELEGRAM and c.external_account_id:
                status = f"{status}"
        else:
            status = t("providers_status_not_connected", lang)
        lines.append(f"• <b>{prov}</b>: {status}")
    return lines


def build_providers_keyboard(
    *,
    lang: str,
    uid: int,
    conns: dict,
    show_skip: bool,
) -> InlineKeyboardMarkup:
    settings = get_settings()
    rows: list[list[InlineKeyboardButton]] = []

    oauth_ok = bool(settings.public_base_url and settings.oauth_state_secret)

    for prov, label_key, kind in (
        (ProviderKind.INSTAGRAM, "providers_connect_instagram", ProviderKind.INSTAGRAM),
        (ProviderKind.LINKEDIN, "providers_connect_linkedin", ProviderKind.LINKEDIN),
    ):
        c = conns.get(prov)
        if c and c.status == ACTIVE:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=t("providers_disconnect", lang).format(provider=prov),
                        callback_data=f"pv:dc:{prov}",
                    )
                ]
            )
        elif oauth_ok:
            url = build_start_url(
                public_base_url=settings.public_base_url,
                secret=settings.oauth_state_secret,
                telegram_user_id=uid,
                provider=kind,
            )
            rows.append(
                [InlineKeyboardButton(text=t(label_key, lang), url=url)]
            )

    tg = conns.get(ProviderKind.TELEGRAM)
    if tg and tg.status == ACTIVE:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("providers_disconnect", lang).format(
                        provider=ProviderKind.TELEGRAM
                    ),
                    callback_data=f"pv:dc:{ProviderKind.TELEGRAM}",
                )
            ]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("providers_connect_telegram", lang),
                    callback_data="pv:tg:link",
                )
            ]
        )

    if show_skip:
        rows.append(
            [InlineKeyboardButton(text=t("providers_skip", lang), callback_data="pv:skip")]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_providers_screen(
    message: Message,
    *,
    lang: str,
    uid: int,
    show_skip: bool = False,
    intro_key: str = "providers_intro",
) -> None:
    async with session_scope() as session:
        conns = await get_connections_map(session, uid)

    lines = _localized_status_lines(conns, lang)
    body = (
        f"<b>{t('providers_title', lang)}</b>\n\n"
        f"{t(intro_key, lang)}\n\n"
        + "\n".join(lines)
        + "\n\n"
    )
    settings = get_settings()
    if not (settings.public_base_url and settings.oauth_state_secret):
        body += t("providers_need_oauth_env", lang) + "\n\n"
    body += t("providers_help", lang)

    keyboard = build_providers_keyboard(
        lang=lang, uid=uid, conns=conns, show_skip=show_skip
    )
    await message.answer(body, reply_markup=keyboard)
