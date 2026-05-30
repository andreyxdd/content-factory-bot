from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import (
    PersonalityProfile,
    ProfileArtifactSet,
    TranslationConsentRecord,
)

CONSENT_POLICY_VERSION = 1


async def get_active_artifact_set(
    session: AsyncSession,
    telegram_user_id: int,
    locale: str,
) -> ProfileArtifactSet | None:
    result = await session.execute(
        select(ProfileArtifactSet).where(
            ProfileArtifactSet.telegram_user_id == telegram_user_id,
            ProfileArtifactSet.locale == locale,
            ProfileArtifactSet.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def activate_artifact_set(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    locale: str,
    profile_version: int,
    style_card_text: str,
    values_block_text: str,
    tribal_block_text: str,
    system_prompt_text: str,
    source_locale: str | None = None,
) -> ProfileArtifactSet:
    await session.execute(
        update(ProfileArtifactSet)
        .where(
            ProfileArtifactSet.telegram_user_id == telegram_user_id,
            ProfileArtifactSet.locale == locale,
            ProfileArtifactSet.is_active.is_(True),
        )
        .values(is_active=False, status="inactive")
    )
    result = await session.execute(
        select(ProfileArtifactSet).where(
            ProfileArtifactSet.telegram_user_id == telegram_user_id,
            ProfileArtifactSet.locale == locale,
            ProfileArtifactSet.profile_version == profile_version,
            ProfileArtifactSet.status == "pending",
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ProfileArtifactSet(
            telegram_user_id=telegram_user_id,
            locale=locale,
            profile_version=profile_version,
            status="active",
            is_active=True,
            source_locale=source_locale,
            style_card_text=style_card_text,
            values_block_text=values_block_text,
            tribal_block_text=tribal_block_text,
            system_prompt_text=system_prompt_text,
        )
        session.add(row)
    else:
        row.status = "active"
        row.is_active = True
        row.source_locale = source_locale
        row.style_card_text = style_card_text
        row.values_block_text = values_block_text
        row.tribal_block_text = tribal_block_text
        row.system_prompt_text = system_prompt_text
        row.error_text = None
    await session.flush()
    return row


async def mark_translation_pending(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    locale: str,
    source_locale: str,
    profile_version: int,
) -> ProfileArtifactSet:
    row = ProfileArtifactSet(
        telegram_user_id=telegram_user_id,
        locale=locale,
        profile_version=profile_version,
        status="pending",
        is_active=False,
        source_locale=source_locale,
        style_card_text=None,
        values_block_text=None,
        tribal_block_text=None,
        system_prompt_text=None,
    )
    session.add(row)
    await session.flush()
    return row


async def mark_translation_failed(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    locale: str,
    error_text: str,
) -> None:
    result = await session.execute(
        select(ProfileArtifactSet)
        .where(
            ProfileArtifactSet.telegram_user_id == telegram_user_id,
            ProfileArtifactSet.locale == locale,
        )
        .order_by(ProfileArtifactSet.id.desc())
    )
    row = result.scalars().first()
    if row is None:
        return
    row.status = "failed"
    row.error_text = error_text
    row.is_active = False


async def get_profile_version(session: AsyncSession, telegram_user_id: int) -> int:
    row = await session.get(PersonalityProfile, telegram_user_id)
    if row is None:
        return 1
    return row.profile_version


async def has_translation_consent(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    source_locale: str,
    target_locale: str,
    policy_version: int = CONSENT_POLICY_VERSION,
) -> bool:
    result = await session.execute(
        select(TranslationConsentRecord.id).where(
            TranslationConsentRecord.telegram_user_id == telegram_user_id,
            TranslationConsentRecord.source_locale == source_locale,
            TranslationConsentRecord.target_locale == target_locale,
            TranslationConsentRecord.policy_version == policy_version,
            TranslationConsentRecord.approved.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


async def record_translation_consent(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    source_locale: str,
    target_locale: str,
    approved: bool,
    action_id: str | None = None,
    policy_version: int = CONSENT_POLICY_VERSION,
) -> TranslationConsentRecord:
    result = await session.execute(
        select(TranslationConsentRecord).where(
            TranslationConsentRecord.telegram_user_id == telegram_user_id,
            TranslationConsentRecord.source_locale == source_locale,
            TranslationConsentRecord.target_locale == target_locale,
            TranslationConsentRecord.policy_version == policy_version,
            TranslationConsentRecord.approved.is_(approved),
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    record = TranslationConsentRecord(
        telegram_user_id=telegram_user_id,
        source_locale=source_locale,
        target_locale=target_locale,
        policy_version=policy_version,
        action_id=action_id or uuid.uuid4().hex,
        approved=approved,
    )
    session.add(record)
    await session.flush()
    return record


async def current_prompt_context(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    locale: str,
    fallback_summary: str,
) -> tuple[str, str]:
    """
    Return prompt context and status.
    Status values: ready | pending | failed | fallback.
    """
    row = await get_active_artifact_set(session, telegram_user_id, locale)
    if row is None:
        return fallback_summary, "fallback"
    if row.status == "pending":
        return fallback_summary, "pending"
    if row.status == "failed":
        return fallback_summary, "failed"
    if row.system_prompt_text:
        return row.system_prompt_text, "ready"
    return fallback_summary, "fallback"

