"""Linear /new session step handlers."""

from __future__ import annotations

import json
import logging

from aiogram.types import CallbackQuery, Message

from content_factory_bot.keyboards.session_flow import (
    angle_choice_keyboard,
    angle_post_pick_keyboard,
    angle_edit_cap_keyboard,
    ending_offer_keyboard,
    ending_pick_keyboard,
    finalize_keyboard,
    partial_publish_retry_keyboard,
    publish_dest_keyboard,
    publish_scope_keyboard,
    tribal_check_keyboard,
)
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.content_session import (
    aggregate_input_text,
    get_latest_draft_round,
    save_for_later,
    set_destinations,
    set_session_state,
)
from content_factory_bot.services.cover import CoverStep
from content_factory_bot.services.draft import AngleOption, DraftOrchestrator
from content_factory_bot.services.providers import list_active_providers
from content_factory_bot.services.publish import PublishOrchestrator
from content_factory_bot.services.session_events import emit
from content_factory_bot.services.session_pipeline import (
    angles_from_storage,
    angles_to_storage,
    expand_angle_to_post,
    process_session_input,
)
from content_factory_bot.services.session_states import (
    AWAITING_ANGLE_CHOICE,
    AWAITING_ANGLE_EDIT,
    AWAITING_ENDING_OFFER,
    AWAITING_ENDING_PICK,
    AWAITING_ENDING_REGEN,
    AWAITING_FINALIZE,
    AWAITING_PUBLISH_DEST,
    AWAITING_PUBLISH_SCOPE,
    AWAITING_TRIBAL_CHECK,
    AWAITING_TRIBAL_FEEDBACK,
    PARTIALLY_PUBLISHED,
    PUBLISHED,
)
from content_factory_bot.services.session_trace import SessionTrace, load_trace, save_trace
from content_factory_bot.services.writing_context import resolve_writing_context

logger = logging.getLogger(__name__)

MAX_EDITS = 3
MAX_TRIBAL = 3


async def load_angles(session, sid: int) -> list[AngleOption]:
    dr = await get_latest_draft_round(session, sid)
    if dr is None:
        return []
    raw = json.loads(dr.options_json)
    if not isinstance(raw, list):
        return []
    return angles_from_storage([str(x) for x in raw])


def _find_angle(angles: list[AngleOption], angle_id: str) -> AngleOption | None:
    for a in angles:
        if a.id.upper() == angle_id.upper():
            return a
    return None


async def persist_selected_angle(
    session, row, angle: AngleOption, trace: SessionTrace
) -> None:
    trace.selected_angle_id = angle.id
    trace.format = angle.format
    trace.hook = angle.hook
    trace.preview = angle.preview
    await save_trace(session, row, trace)


async def show_full_post(
    target: Message | CallbackQuery,
    *,
    lang: str,
    text: str,
    session_id: int,
) -> None:
    msg = target if isinstance(target, Message) else target.message
    assert msg is not None
    await msg.answer(text)
    await msg.answer(
        t("session_ending_offer", lang),
        reply_markup=ending_offer_keyboard(session_id, lang),
    )


async def handle_angle_callback(
    callback: CallbackQuery,
    session,
    row,
    *,
    sid: int,
    uid: int,
    lang: str,
    action: str,
) -> None:
    angles = await load_angles(session, sid)
    trace = load_trace(row)

    if action in ("A", "B", "C"):
        angle = _find_angle(angles, action)
        if angle is None:
            await callback.answer()
            return
        await persist_selected_angle(session, row, angle, trace)
        emit("angle_selected", session_id=sid, telegram_user_id=uid, angle=action)
        await set_session_state(session, row, AWAITING_ANGLE_CHOICE)
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_edit_or_expand", lang),
            reply_markup=angle_post_pick_keyboard(sid, lang),
        )
        await callback.answer()
        return

    if action == "edit":
        if trace.selected_angle_id is None:
            await callback.answer(t("session_pick_angle_first", lang), show_alert=True)
            return
        if trace.edit_count >= MAX_EDITS:
            await callback.message.answer(  # type: ignore[union-attr]
                t("session_edit_cap", lang),
                reply_markup=angle_edit_cap_keyboard(sid, lang),
            )
            await callback.answer()
            return
        await set_session_state(session, row, AWAITING_ANGLE_EDIT)
        await callback.message.answer(t("session_edit_prompt", lang))  # type: ignore[union-attr]
        await callback.answer()
        return

    if action == "expand":
        angle = _find_angle(angles, trace.selected_angle_id or "")
        if angle is None:
            await callback.answer()
            return
        await callback.message.answer(t("session_stage_expanding", lang))  # type: ignore[union-attr]
        post = await expand_angle_to_post(session, row, angle)
        row.final_draft_text = post
        await session.commit()
        await set_session_state(session, row, AWAITING_ENDING_OFFER)
        await show_full_post(callback, lang=lang, text=post, session_id=sid)
        await callback.answer()
        return

    if action == "restart":
        await callback.message.answer(t("session_stage_angles", lang))  # type: ignore[union-attr]
        rnd, new_angles = await process_session_input(session, row)
        from content_factory_bot.services.draft_delivery import deliver_angle_round

        await deliver_angle_round(
            telegram_user_id=uid,
            session_id=sid,
            round_no=rnd,
            angles=new_angles,
            lang=lang,
            session=session,
            message=callback.message,
        )
        await callback.answer()
        return

    await callback.answer()


async def handle_angle_edit_text(
    message: Message, session, row, *, uid: int, lang: str, instruction: str
) -> None:
    trace = load_trace(row)
    angles = await load_angles(session, row.id)
    angle = _find_angle(angles, trace.selected_angle_id or "")
    if angle is None:
        return
    ctx = await resolve_writing_context(
        session, telegram_user_id=uid, locale=lang, content_session=row
    )
    input_text = await aggregate_input_text(session, row.id)
    orch = DraftOrchestrator()
    updated = await orch.edit_selected_angle(
        system_prompt=ctx.system_prompt,
        style_card=ctx.style_card,
        content_language=lang,
        input_text=input_text,
        angle=angle,
        edit_instruction=instruction,
    )
    trace.edit_count += 1
    trace.edit_history.append(instruction[:500])
    await persist_selected_angle(session, row, updated, trace)
    emit(
        "edit_selected_submitted",
        session_id=row.id,
        telegram_user_id=uid,
        edit_count=trace.edit_count,
    )
    dr = await get_latest_draft_round(session, row.id)
    if dr:
        stored = await load_angles(session, row.id)
        replaced = [updated if a.id.upper() == updated.id.upper() else a for a in stored]
        dr.options_json = json.dumps(angles_to_storage(replaced))
        await session.commit()
    await set_session_state(session, row, AWAITING_ANGLE_CHOICE)
    block = updated.display_block(lang)
    await message.answer(
        f"{t('session_angle_updated', lang)}\n\n{block}",
        reply_markup=angle_choice_keyboard(row.id, lang),
    )


async def handle_ending_callback(
    callback: CallbackQuery,
    session,
    row,
    *,
    sid: int,
    uid: int,
    lang: str,
    action: str,
    fsm_data: dict,
) -> None:
    text = row.final_draft_text or ""
    ctx = await resolve_writing_context(
        session, telegram_user_id=uid, locale=lang, content_session=row
    )
    orch = DraftOrchestrator()
    trace = load_trace(row)

    if action == "yes":
        q, p = await orch.generate_two_endings(
            system_prompt=ctx.system_prompt,
            style_card=ctx.style_card,
            content_language=lang,
            full_post=text,
        )
        fsm_data["ending_q"] = q
        fsm_data["ending_p"] = p
        await set_session_state(session, row, AWAITING_ENDING_PICK)
        await callback.message.answer(  # type: ignore[union-attr]
            f"{t('session_ending_q', lang)}\n{q}\n\n{t('session_ending_p', lang)}\n{p}",
            reply_markup=ending_pick_keyboard(sid, lang),
        )
        await callback.answer()
        return

    if action == "no":
        await _goto_tribal(callback, session, row, sid, lang)
        await callback.answer()
        return

    if action == "q":
        row.final_draft_text = await orch.replace_final_paragraph(
            full_post=text, new_paragraph=fsm_data.get("ending_q", "")
        )
        trace.ending_variant = "question"
        await save_trace(session, row, trace)
        emit("ending_ab_chosen", session_id=sid, telegram_user_id=uid, variant="question")
        await _goto_tribal(callback, session, row, sid, lang)
        await callback.answer()
        return

    if action == "p":
        row.final_draft_text = await orch.replace_final_paragraph(
            full_post=text, new_paragraph=fsm_data.get("ending_p", "")
        )
        trace.ending_variant = "punch"
        await save_trace(session, row, trace)
        emit("ending_ab_chosen", session_id=sid, telegram_user_id=uid, variant="punch")
        await _goto_tribal(callback, session, row, sid, lang)
        await callback.answer()
        return

    if action == "regen":
        await set_session_state(session, row, AWAITING_ENDING_REGEN)
        await callback.message.answer(t("session_ending_regen_prompt", lang))  # type: ignore[union-attr]
        await callback.answer()
        return

    await callback.answer()


async def _goto_tribal(
    target: Message | CallbackQuery, session, row, sid: int, lang: str
) -> None:
    await set_session_state(session, row, AWAITING_TRIBAL_CHECK)
    msg = target if isinstance(target, Message) else target.message
    assert msg is not None
    await msg.answer(
        t("session_tribal_prompt", lang),
        reply_markup=tribal_check_keyboard(sid, lang),
    )


async def handle_ending_regen_text(
    message: Message,
    session,
    row,
    *,
    uid: int,
    lang: str,
    instruction: str,
    fsm: dict,
) -> None:
    ctx = await resolve_writing_context(
        session, telegram_user_id=uid, locale=lang, content_session=row
    )
    orch = DraftOrchestrator()
    q, p = await orch.generate_two_endings(
        system_prompt=ctx.system_prompt,
        style_card=ctx.style_card,
        content_language=lang,
        full_post=row.final_draft_text or "",
    )
    fsm["ending_q"] = q
    fsm["ending_p"] = p
    await set_session_state(session, row, AWAITING_ENDING_PICK)
    await message.answer(
        f"{t('session_ending_q', lang)}\n{q}\n\n{t('session_ending_p', lang)}\n{p}",
        reply_markup=ending_pick_keyboard(row.id, lang),
    )


async def handle_tribal_callback(
    callback: CallbackQuery, session, row, *, sid: int, uid: int, lang: str, yes: bool
) -> bool:
    if yes:
        await set_session_state(session, row, AWAITING_FINALIZE)
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_finalize_prompt", lang),
            reply_markup=finalize_keyboard(sid, lang),
        )
        await callback.answer()
        return False
    trace = load_trace(row)
    if trace.tribal_rewrite_count >= MAX_TRIBAL:
        await callback.message.answer(t("session_tribal_cap", lang))  # type: ignore[union-attr]
        await set_session_state(session, row, AWAITING_FINALIZE)
        await callback.message.answer(
            t("session_finalize_prompt", lang),
            reply_markup=finalize_keyboard(sid, lang),
        )
        await callback.answer()
        return False
    await set_session_state(session, row, AWAITING_TRIBAL_FEEDBACK)
    await callback.message.answer(t("session_tribal_feedback_prompt", lang))  # type: ignore[union-attr]
    await callback.answer()
    return True  # caller should set FSM tribal_feedback


async def handle_tribal_feedback_text(
    message: Message, session, row, *, uid: int, lang: str, feedback: str
) -> None:
    trace = load_trace(row)
    ctx = await resolve_writing_context(
        session, telegram_user_id=uid, locale=lang, content_session=row
    )
    orch = DraftOrchestrator()
    post = await orch.rewrite_post_with_feedback(
        system_prompt=ctx.system_prompt,
        style_card=ctx.style_card,
        content_language=lang,
        full_post=row.final_draft_text or "",
        feedback=feedback,
    )
    row.final_draft_text = post
    trace.tribal_rewrite_count += 1
    await save_trace(session, row, trace)
    emit("tribal_rewrite", session_id=row.id, telegram_user_id=uid, count=trace.tribal_rewrite_count)
    await set_session_state(session, row, AWAITING_TRIBAL_CHECK)
    await message.answer(post)
    await message.answer(
        t("session_tribal_prompt", lang),
        reply_markup=tribal_check_keyboard(row.id, lang),
    )


async def handle_finalize_callback(
    callback: CallbackQuery,
    session,
    row,
    *,
    sid: int,
    uid: int,
    lang: str,
    action: str,
    fsm_data: dict,
) -> None:
    if action == "save":
        trace = load_trace(row)
        await save_for_later(
            session,
            row,
            final_text=row.final_draft_text or "",
            trace_json=trace.to_json(),
        )
        emit("saved_content", session_id=sid, telegram_user_id=uid)
        await callback.message.answer(t("session_saved_content", lang))  # type: ignore[union-attr]
        await callback.answer()
        return

    if action == "post":
        connected = await list_active_providers(session, uid)
        if not connected:
            await callback.answer(t("providers_setup_required", lang), show_alert=True)
            return
        await set_session_state(session, row, AWAITING_PUBLISH_SCOPE)
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_publish_scope", lang),
            reply_markup=publish_scope_keyboard(sid, lang),
        )
        await callback.answer()
        return

    await callback.answer()


async def handle_publish_callback(
    callback: CallbackQuery,
    session,
    row,
    *,
    sid: int,
    uid: int,
    lang: str,
    action: str,
    fsm_data: dict,
    bot,
) -> None:
    connected = await list_active_providers(session, uid)

    if action == "all":
        fsm_data["publish_destinations"] = list(connected)
        await _do_publish(callback, session, row, sid, uid, lang, bot, fsm_data["publish_destinations"])
        await callback.answer()
        return

    if action == "choose":
        fsm_data["publish_destinations"] = list(connected)
        await set_session_state(session, row, AWAITING_PUBLISH_DEST)
        await callback.message.edit_reply_markup(  # type: ignore[union-attr]
            reply_markup=publish_dest_keyboard(
                sid, lang, connected, set(connected)
            )
        )
        await callback.answer()
        return

    if action == "go":
        dests = fsm_data.get("publish_destinations") or []
        if not dests:
            await callback.answer(t("session_destinations_required", lang), show_alert=True)
            return
        await set_destinations(session, row, dests)
        await _do_publish(callback, session, row, sid, uid, lang, bot, dests)
        await callback.answer()
        return

    await callback.answer()


async def handle_publish_retry(
    callback: CallbackQuery,
    session,
    row,
    *,
    sid: int,
    uid: int,
    lang: str,
    provider: str,
    bot,
) -> None:
    await _do_publish(
        callback, session, row, sid, uid, lang, bot, [provider]
    )


async def handle_publish_dest_toggle(
    callback: CallbackQuery,
    session,
    row,
    *,
    sid: int,
    uid: int,
    lang: str,
    provider: str,
    fsm_data: dict,
) -> None:
    connected = await list_active_providers(session, uid)
    selected = set(fsm_data.get("publish_destinations") or connected)
    if provider in selected:
        selected.discard(provider)
    else:
        selected.add(provider)
    if not selected:
        await callback.answer(t("session_destinations_required", lang), show_alert=True)
        return
    fsm_data["publish_destinations"] = [p for p in connected if p in selected]
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=publish_dest_keyboard(sid, lang, connected, set(fsm_data["publish_destinations"]))
    )
    await callback.answer()


async def _do_publish(
    callback: CallbackQuery,
    session,
    row,
    sid: int,
    uid: int,
    lang: str,
    bot,
    destinations: list[str],
) -> None:
    text = row.final_draft_text
    if not text:
        return
    emit("publish_attempt", session_id=sid, telegram_user_id=uid, destinations=destinations)
    if row.cover_generation and not row.cover_storage_ref:
        cover_ref = await CoverStep().generate(draft_text=text, session_id=sid)
        row.cover_storage_ref = cover_ref
        await session.commit()
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_cover_ready", lang).format(ref=cover_ref)
        )
    results = await PublishOrchestrator(bot=bot).publish_session(
        session,
        session_id=sid,
        telegram_user_id=uid,
        draft_text=text,
        providers=destinations,
    )
    ok = [r for r in results if r.url and not r.error]
    failed = [r for r in results if r.error or not r.url]
    emit(
        "publish_result",
        session_id=sid,
        telegram_user_id=uid,
        ok=len(ok),
        failed=len(failed),
    )
    lines = "\n".join(
        f"• <b>{r.provider}</b>: {r.url or r.error or '—'}" for r in results
    )
    if failed and ok:
        row.state = PARTIALLY_PUBLISHED
        row.is_active = True
        await session.commit()
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_partial_published", lang).format(links=lines),
            reply_markup=partial_publish_retry_keyboard(
                sid, lang, [r.provider for r in failed]
            ),
        )
        return
    row.state = PUBLISHED
    row.is_active = False
    await session.commit()
    await callback.message.answer(t("session_published", lang).format(links=lines))  # type: ignore[union-attr]
