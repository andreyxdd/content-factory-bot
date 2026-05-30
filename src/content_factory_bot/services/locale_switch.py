from __future__ import annotations

import asyncio

from content_factory_bot.db.models import Creator, PersonalityProfile
from content_factory_bot.db.session import session_scope
from content_factory_bot.services.profile_artifacts import (
    activate_artifact_set,
    get_active_artifact_set,
    get_profile_version,
    mark_translation_failed,
    mark_translation_pending,
)
from content_factory_bot.services.translation import ArtifactBundle, ArtifactTranslator


async def trigger_locale_translation(
    *,
    telegram_user_id: int,
    source_locale: str,
    target_locale: str,
) -> None:
    async with session_scope() as session:
        source = await get_active_artifact_set(session, telegram_user_id, source_locale)
        if source is None:
            profile = await session.get(PersonalityProfile, telegram_user_id)
            if profile is None:
                return
            source_bundle = ArtifactBundle(
                style_card_text=profile.style_card_text or "",
                values_block_text=profile.values_block_text or "",
                tribal_block_text=profile.tribal_block_text or "",
                system_prompt_text=profile.system_prompt_text or "",
            )
            profile_version = profile.profile_version
        else:
            source_bundle = ArtifactBundle(
                style_card_text=source.style_card_text or "",
                values_block_text=source.values_block_text or "",
                tribal_block_text=source.tribal_block_text or "",
                system_prompt_text=source.system_prompt_text or "",
            )
            profile_version = source.profile_version

    translator = ArtifactTranslator()
    try:
        translated = await translator.translate_bundle(
            source_locale=source_locale,
            target_locale=target_locale,
            bundle=source_bundle,
        )
    except Exception as exc:
        async with session_scope() as session:
            creator = await session.get(Creator, telegram_user_id)
            if creator:
                creator.primary_language = source_locale
            await mark_translation_failed(
                session,
                telegram_user_id=telegram_user_id,
                locale=target_locale,
                error_text=str(exc),
            )
        return

    async with session_scope() as session:
        await activate_artifact_set(
            session,
            telegram_user_id=telegram_user_id,
            locale=target_locale,
            profile_version=profile_version,
            source_locale=source_locale,
            style_card_text=translated.style_card_text,
            values_block_text=translated.values_block_text,
            tribal_block_text=translated.tribal_block_text,
            system_prompt_text=translated.system_prompt_text,
        )


async def switch_locale_with_pending_translation(
    *,
    telegram_user_id: int,
    source_locale: str,
    target_locale: str,
) -> None:
    async with session_scope() as session:
        creator = await session.get(Creator, telegram_user_id)
        if creator is None:
            return
        creator.primary_language = target_locale
        profile_version = await get_profile_version(session, telegram_user_id)
        await mark_translation_pending(
            session,
            telegram_user_id=telegram_user_id,
            locale=target_locale,
            source_locale=source_locale,
            profile_version=profile_version,
        )
    asyncio.create_task(
        trigger_locale_translation(
            telegram_user_id=telegram_user_id,
            source_locale=source_locale,
            target_locale=target_locale,
        )
    )
