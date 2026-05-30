from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_factory_bot.db.models import Creator, PersonalityProfile, ProfileAnswer, PrimaryLanguage
from content_factory_bot.services.onboarding_engine import (
    ordered_profile_keys,
    required_answer_keys,
)


async def save_answer(
    session: AsyncSession,
    telegram_user_id: int,
    question_key: str,
    answer_text: str,
    option_index: int | None,
    is_custom: bool,
) -> None:
    result = await session.execute(
        select(ProfileAnswer).where(
            ProfileAnswer.telegram_user_id == telegram_user_id,
            ProfileAnswer.question_key == question_key,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ProfileAnswer(
            telegram_user_id=telegram_user_id,
            question_key=question_key,
            answer_text=answer_text,
            option_index=option_index,
            is_custom=is_custom,
        )
        session.add(row)
    else:
        row.answer_text = answer_text
        row.option_index = option_index
        row.is_custom = is_custom
    await session.commit()


async def get_answered_keys(session: AsyncSession, telegram_user_id: int) -> set[str]:
    result = await session.execute(
        select(ProfileAnswer.question_key).where(
            ProfileAnswer.telegram_user_id == telegram_user_id
        )
    )
    return set(result.scalars().all())


async def get_profile_answers_map(session: AsyncSession, telegram_user_id: int) -> dict[str, str]:
    result = await session.execute(
        select(ProfileAnswer.question_key, ProfileAnswer.answer_text).where(
            ProfileAnswer.telegram_user_id == telegram_user_id
        )
    )
    rows = result.all()
    return {question_key: answer_text for question_key, answer_text in rows}


async def is_profile_complete(session: AsyncSession, telegram_user_id: int) -> bool:
    answered = await get_answered_keys(session, telegram_user_id)
    required = required_answer_keys()
    return required.issubset(answered)


async def mark_profile_ready(session: AsyncSession, telegram_user_id: int) -> None:
    profile = await session.get(PersonalityProfile, telegram_user_id)
    if profile is None:
        profile = PersonalityProfile(telegram_user_id=telegram_user_id, ready=True)
        session.add(profile)
    else:
        profile.ready = True
        profile.profile_version += 1
    await session.commit()


async def is_profile_ready(session: AsyncSession, telegram_user_id: int) -> bool:
    profile = await session.get(PersonalityProfile, telegram_user_id)
    return bool(profile and profile.ready)


async def _get_answer(
    session: AsyncSession, telegram_user_id: int, question_key: str
) -> ProfileAnswer | None:
    result = await session.execute(
        select(ProfileAnswer).where(
            ProfileAnswer.telegram_user_id == telegram_user_id,
            ProfileAnswer.question_key == question_key,
        )
    )
    return result.scalar_one_or_none()


def _yes_no_from_answer(option_index: int | None, default: bool = True) -> bool:
    if option_index is None:
        return default
    return option_index == 0


async def apply_creator_preferences(session: AsyncSession, telegram_user_id: int) -> None:
    creator = await session.get(Creator, telegram_user_id)
    if creator is None:
        return

    lang_ans = await _get_answer(session, telegram_user_id, "primary_language")
    if lang_ans and lang_ans.option_index is not None:
        creator.primary_language = (
            PrimaryLanguage.RU if lang_ans.option_index == 1 else PrimaryLanguage.EN
        )

    research = await _get_answer(session, telegram_user_id, "web_research")
    if research:
        creator.research_default_enabled = _yes_no_from_answer(research.option_index, True)

    review = await _get_answer(session, telegram_user_id, "review_agent")
    if review:
        creator.review_enabled = _yes_no_from_answer(review.option_index, True)

    await session.commit()


async def format_profile_summary(session: AsyncSession, telegram_user_id: int, lang: str) -> str:
    lines: list[str] = []
    for key in ordered_profile_keys():
        ans = await _get_answer(session, telegram_user_id, key)
        if ans:
            lines.append(f"<b>{key}</b>\n{ans.answer_text}")
    return "\n\n".join(lines) if lines else "—"


async def save_profile_artifacts(
    session: AsyncSession,
    telegram_user_id: int,
    *,
    style_card_text: str,
    values_block_text: str,
    tribal_block_text: str,
    system_prompt_text: str,
) -> None:
    profile = await session.get(PersonalityProfile, telegram_user_id)
    if profile is None:
        profile = PersonalityProfile(telegram_user_id=telegram_user_id, ready=False)
        session.add(profile)
    profile.style_card_text = style_card_text
    profile.values_block_text = values_block_text
    profile.tribal_block_text = tribal_block_text
    profile.system_prompt_text = system_prompt_text
    await session.commit()
