import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from content_factory_bot.config import get_settings
from content_factory_bot.db.models import ContentSession, Creator
from content_factory_bot.db.session import session_scope
from content_factory_bot.keyboards.draft import (
    draft_options_keyboard,
    follow_up_keyboard,
    publish_keyboard,
    session_delete_confirm_keyboard,
    sessions_list_keyboard,
)
from content_factory_bot.keyboards.session_flow import finalize_keyboard, setup_keyboard
from content_factory_bot.services.session_states import is_legacy_state
from content_factory_bot.services.system_prompt import (
    MAX_SYSTEM_PROMPT_ADDITION_LEN,
    validate_system_prompt_addition,
)
from content_factory_bot.services.linear_session_handler import (
    handle_angle_callback,
    handle_angle_edit_text,
    handle_ending_callback,
    handle_finalize_callback,
    handle_publish_callback,
    handle_publish_dest_toggle,
    handle_publish_retry,
    handle_tribal_callback,
    handle_tribal_feedback_text,
)
from content_factory_bot.locale.i18n import t
from content_factory_bot.locale.telegram_html import escape_html
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.content_session import (
    aggregate_input_text,
    delete_session,
    get_active_session,
    get_latest_draft_round,
    get_session_by_id,
    list_recent_sessions,
    next_round_no,
    parse_options,
    resume_session,
    save_draft_round,
    save_media_input,
    save_text_input,
    select_draft_option,
    set_final_draft,
    set_session_state,
    start_session,
)
from content_factory_bot.services.cover import CoverStep
from content_factory_bot.services.draft import DraftOrchestrator
from content_factory_bot.handlers.providers_screen import send_providers_screen
from content_factory_bot.services.profile import format_profile_summary, is_profile_ready
from content_factory_bot.services.profile_artifacts import current_prompt_context
from content_factory_bot.services.providers import is_setup_complete
from content_factory_bot.services.publish import PublishOrchestrator
from content_factory_bot.services.draft_delivery import deliver_angle_round
from content_factory_bot.services.session_pipeline import process_session_input
from content_factory_bot.services.telegram_notify import notify_creator
from content_factory_bot.services.stt import transcribe_audio
from content_factory_bot.services.telegram_files import download_file_bytes
from content_factory_bot.services.vision import describe_image
from content_factory_bot.worker.queue import JobQueue

router = Router(name="content_session")


class NewSessionStates(StatesGroup):
    setup = State()
    instructions = State()


def _setup_fsm_flags(fsm: dict) -> tuple[bool, bool, bool]:
    research = bool(fsm.get("research", True))
    cover = bool(fsm.get("cover", False))
    has_instructions = bool((fsm.get("session_prompt_addition") or "").strip())
    return research, cover, has_instructions


async def _reply_session_setup(
    target: Message,
    state: FSMContext,
    *,
    lang: str,
    edit: bool = False,
) -> None:
    fsm = await state.get_data()
    research, cover, has_instructions = _setup_fsm_flags(fsm)
    text = t("session_setup_intro", lang)
    addition = (fsm.get("session_prompt_addition") or "").strip()
    if addition:
        preview = addition[:120] + ("…" if len(addition) > 120 else "")
        text += "\n\n" + t("session_instructions_current", lang).format(preview=preview)
    kb = setup_keyboard(
        lang, research=research, cover=cover, has_instructions=has_instructions
    )
    if edit and hasattr(target, "edit_text"):
        await target.edit_text(text, reply_markup=kb)  # type: ignore[union-attr]
    else:
        await target.answer(text, reply_markup=kb)


class SessionCustomStates(StatesGroup):
    draft_custom = State()


class SessionFlowStates(StatesGroup):
    angle_edit = State()
    tribal_feedback = State()
    ending_regen = State()


def _lang(data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


@router.message(Command("new"))
async def cmd_new(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    lang = _lang(data)
    uid = message.from_user.id
    async with session_scope() as session:
        if not await is_profile_ready(session, uid):
            await message.answer(t("onboarding_required", lang))
            return
        if not await is_setup_complete(session, uid):
            await message.answer(t("providers_setup_required", lang))
            await send_providers_screen(
                message, lang=lang, uid=uid, show_skip=True
            )
            return
        if await get_active_session(session, uid):
            await message.answer(t("session_active_exists", lang))
            return
        creator = await session.get(Creator, uid)
        research = creator.research_default_enabled if creator else True

    await state.set_state(NewSessionStates.setup)
    await state.update_data(research=research, cover=False, session_prompt_addition="")
    await _reply_session_setup(message, state, lang=lang)


@router.callback_query(NewSessionStates.setup, F.data.startswith("cs:"))
async def on_session_setup(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    lang = _lang(data)
    uid = callback.from_user.id
    fsm = await state.get_data()
    research, cover, has_instructions = _setup_fsm_flags(fsm)
    addition = (fsm.get("session_prompt_addition") or "").strip() or None

    if callback.data == "cs:toggle:research":
        await state.update_data(research=not research)
        await _reply_session_setup(
            callback.message, state, lang=lang, edit=True  # type: ignore[arg-type]
        )
        await callback.answer()
        return

    if callback.data == "cs:toggle:cover":
        await state.update_data(cover=not cover)
        await _reply_session_setup(
            callback.message, state, lang=lang, edit=True  # type: ignore[arg-type]
        )
        await callback.answer()
        return

    if callback.data == "cs:setup:instructions":
        await state.set_state(NewSessionStates.instructions)
        prompt = t("session_instructions_prompt", lang).format(
            max_len=MAX_SYSTEM_PROMPT_ADDITION_LEN
        )
        if addition:
            preview = addition[:200] + ("…" if len(addition) > 200 else "")
            prompt += "\n\n" + t("session_instructions_current", lang).format(
                preview=preview
            )
        await callback.message.answer(prompt)  # type: ignore[union-attr]
        await callback.answer()
        return

    if callback.data == "cs:setup:clear_instructions":
        await state.update_data(session_prompt_addition="")
        await _reply_session_setup(
            callback.message, state, lang=lang, edit=True  # type: ignore[arg-type]
        )
        await callback.answer(t("session_instructions_cleared", lang))
        return

    if callback.data == "cs:start":
        async with session_scope() as session:
            row = await start_session(
                session,
                uid,
                web_research=research,
                cover_generation=cover,
                destinations=[],
                session_prompt_addition=addition,
            )
        await state.clear()
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_send_input", lang).format(id=row.id)
        )
        await callback.answer()
        return

    await callback.answer()


@router.message(NewSessionStates.instructions, F.text)
async def on_session_instructions_text(
    message: Message, state: FSMContext, **data
) -> None:
    if not message.from_user or not message.text:
        return
    lang = _lang(data)
    text = message.text.strip()
    if text.startswith("/"):
        return
    err = validate_system_prompt_addition(text)
    if err == "too_long":
        await message.answer(
            t("session_instructions_too_long", lang).format(
                max_len=MAX_SYSTEM_PROMPT_ADDITION_LEN
            )
        )
        return
    await state.update_data(session_prompt_addition=text)
    await state.set_state(NewSessionStates.setup)
    await message.answer(t("session_instructions_saved", lang))
    await _reply_session_setup(message, state, lang=lang)


@router.message(F.text)
async def on_text_message(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user or not message.text:
        return
    if message.text.startswith("/"):
        return

    lang = _lang(data)
    uid = message.from_user.id
    fsm_state = await state.get_state()

    if fsm_state == SessionFlowStates.angle_edit.state:
        fsm = await state.get_data()
        sid = int(fsm["session_id"])
        async with session_scope() as session:
            row = await get_session_by_id(session, sid, uid)
            if row is None:
                await state.clear()
                await message.answer(t("session_not_found", lang))
                return
            await handle_angle_edit_text(
                message, session, row, uid=uid, lang=lang, instruction=message.text
            )
        await state.clear()
        return

    if fsm_state == SessionFlowStates.tribal_feedback.state:
        fsm = await state.get_data()
        sid = int(fsm["session_id"])
        async with session_scope() as session:
            row = await get_session_by_id(session, sid, uid)
            if row is None:
                await state.clear()
                return
            await handle_tribal_feedback_text(
                message, session, row, uid=uid, lang=lang, feedback=message.text
            )
        await state.clear()
        return

    if fsm_state == SessionFlowStates.ending_regen.state:
        fsm = await state.get_data()
        sid = int(fsm["session_id"])
        async with session_scope() as session:
            row = await get_session_by_id(session, sid, uid)
            if row is None:
                await state.clear()
                return
            from content_factory_bot.services.linear_session_handler import (
                handle_ending_regen_text,
            )

            await handle_ending_regen_text(
                message, session, row, uid=uid, lang=lang, instruction=message.text, fsm=fsm
            )
        await state.clear()
        return

    if fsm_state == SessionCustomStates.draft_custom.state:
        fsm = await state.get_data()
        sid = int(fsm["session_id"])
        async with session_scope() as session:
            row = await get_session_by_id(session, sid, uid)
            if row is None:
                await state.clear()
                await message.answer(t("session_not_found", lang))
                return
            await set_final_draft(session, row, message.text)
            await _after_confirm(message, session, row, lang)
        await state.clear()
        return

    async with session_scope() as session:
        row = await get_active_session(session, uid)
        if row is None:
            return
        if row.state == "awaiting_input":
            await save_text_input(session, row.id, message.text)
            await _run_drafts(message, session, row, lang, uid)
            return
        if row.state == "awaiting_custom_draft":
            row.final_draft_text = message.text
            await session.commit()
            await set_session_state(session, row, "awaiting_follow_up")
            await message.answer(
                t("draft_custom_saved", lang),
                reply_markup=follow_up_keyboard(row.id, lang),
            )
            return


@router.message(F.photo)
async def on_photo(message: Message, **data) -> None:
    if not message.from_user or not message.photo:
        return
    lang = _lang(data)
    uid = message.from_user.id
    file_id = message.photo[-1].file_id
    transcript = t("session_image_stub", lang)
    if message.bot:
        try:
            raw = await download_file_bytes(message.bot, file_id)
            transcript = await describe_image(raw, mime="image/jpeg")
        except Exception:
            pass
    async with session_scope() as session:
        row = await get_active_session(session, uid)
        if row is None or row.state != "awaiting_input":
            return
        await save_media_input(
            session,
            row.id,
            input_type="image",
            transcript=transcript,
            storage_ref=file_id,
        )
        agg = await aggregate_input_text(session, row.id)
        has_text = await _has_text_input(session, row.id)
        if agg.strip() and not has_text:
            await message.answer(t("session_image_drafting", lang))
            await _run_drafts(message, session, row, lang, uid)
            return
    await message.answer(t("session_image_received", lang))


@router.message(F.voice | F.audio)
async def on_voice(message: Message, **data) -> None:
    if not message.from_user:
        return
    lang = _lang(data)
    uid = message.from_user.id
    ref = None
    mime = "audio/ogg"
    if message.voice:
        ref = message.voice.file_id
    elif message.audio:
        ref = message.audio.file_id
        mime = "audio/mpeg"
    if not ref:
        return
    transcript = t("session_voice_stub", lang)
    if message.bot:
        try:
            raw = await download_file_bytes(message.bot, ref)
            transcript = await transcribe_audio(raw, mime=mime)
        except Exception:
            pass
    async with session_scope() as session:
        row = await get_active_session(session, uid)
        if row is None or row.state != "awaiting_input":
            return
        await save_media_input(
            session,
            row.id,
            input_type="voice",
            transcript=transcript,
            storage_ref=ref,
        )
        if transcript.strip():
            await message.answer(t("session_voice_drafting", lang))
            await _run_drafts(message, session, row, lang, uid)
            return
    await message.answer(t("session_voice_received", lang))


async def _has_text_input(session, session_id: int) -> bool:
    from sqlalchemy import select

    from content_factory_bot.db.models import SessionInput

    result = await session.execute(
        select(SessionInput.id)
        .where(
            SessionInput.session_id == session_id,
            SessionInput.input_type == "text",
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _draft_timeout_watch(
    session_id: int,
    uid: int,
    lang: str,
    *,
    timeout_sec: float = 120.0,
) -> None:
    await asyncio.sleep(timeout_sec)
    async with session_scope() as session:
        row = await get_session_by_id(session, session_id, uid)
        if row is None or row.state != "drafting":
            return
    await notify_creator(uid, t("session_drafting_timeout", lang))


async def _run_drafts(
    message: Message,
    session,
    row,
    lang: str,
    uid: int,
) -> None:
    settings = get_settings()
    if settings.use_worker:
        await set_session_state(session, row, "drafting")
        q = JobQueue(settings.redis_url)
        await q.connect()
        try:
            await q.enqueue(
                "draft_round",
                {"session_id": row.id, "telegram_user_id": uid},
            )
        finally:
            await q.close()
        await message.answer(t("session_drafting_queued", lang))
        asyncio.create_task(
            _draft_timeout_watch(row.id, uid, lang, timeout_sec=120.0)
        )
        return

    await message.answer(t("session_stage_angles", lang))
    rnd, angles = await process_session_input(session, row)
    await deliver_angle_round(
        telegram_user_id=uid,
        session_id=row.id,
        round_no=rnd,
        angles=angles,
        lang=lang,
        session=session,
        message=message,
    )


def _session_delete_confirm_text(row: ContentSession, lang: str) -> str:
    raw_title = (row.title or "").strip() or t("session_untitled", lang)
    return t("session_delete_confirm", lang).format(
        title=escape_html(raw_title[:80]),
        id=row.id,
        state=escape_html(row.state),
    )


async def _refresh_sessions_list_message(
    callback: CallbackQuery, uid: int, lang: str
) -> None:
    if not callback.message:
        return
    async with session_scope() as session:
        rows = await list_recent_sessions(session, uid, limit=10)
    if not rows:
        await callback.message.edit_text(t("sessions_list_empty_after_delete", lang))
        return
    pairs = [(r.id, r.title, r.state) for r in rows]
    await callback.message.edit_text(
        t("sessions_list", lang),
        reply_markup=sessions_list_keyboard(pairs, lang),
    )


@router.callback_query(F.data.startswith("cs:"))
async def on_session_callback(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data:
        return
    lang = _lang(data)
    uid = callback.from_user.id
    parts = callback.data.split(":")

    if parts[1] == "resume" and len(parts) == 3:
        sid = int(parts[2])
        async with session_scope() as session:
            row = await resume_session(session, sid, uid)
            if row is None:
                await callback.answer(t("session_not_found", lang), show_alert=True)
                return
            if row.state == "ready_to_publish_later":
                await callback.message.answer(  # type: ignore[union-attr]
                    t("session_finalize_prompt", lang),
                    reply_markup=finalize_keyboard(row.id, lang),
                )
            else:
                await callback.message.answer(  # type: ignore[union-attr]
                    t("session_resumed", lang).format(id=row.id, state=row.state)
                )
        await callback.answer()
        return

    if parts[1] == "del" and len(parts) == 3:
        sid = int(parts[2])
        async with session_scope() as session:
            row = await get_session_by_id(session, sid, uid)
            if row is None:
                await callback.answer(t("session_not_found", lang), show_alert=True)
                return
        if callback.message:
            await callback.message.edit_text(
                _session_delete_confirm_text(row, lang),
                reply_markup=session_delete_confirm_keyboard(sid, lang),
            )
        await callback.answer()
        return

    if parts[1] == "delok" and len(parts) == 3:
        sid = int(parts[2])
        async with session_scope() as session:
            row = await delete_session(session, sid, uid)
            if row is None:
                await callback.answer(t("session_not_found", lang), show_alert=True)
                return
        await _refresh_sessions_list_message(callback, uid, lang)
        await callback.answer(t("session_deleted", lang))
        return

    if parts[1] == "dellist":
        await _refresh_sessions_list_message(callback, uid, lang)
        await callback.answer()
        return

    if len(parts) < 3:
        await callback.answer()
        return

    sid = int(parts[1])

    async with session_scope() as session:
        row = await get_session_by_id(session, sid, uid)
        if row is None:
            await callback.answer(t("session_not_found", lang), show_alert=True)
            return

        fsm_data = await state.get_data()
        if not is_legacy_state(row.state):
            if parts[2] == "angle" and len(parts) == 4:
                action = parts[3]
                if action == "edit":
                    await state.set_state(SessionFlowStates.angle_edit)
                    await state.update_data(session_id=sid)
                await handle_angle_callback(
                    callback, session, row, sid=sid, uid=uid, lang=lang, action=action
                )
                return
            if parts[2] == "ending" and len(parts) == 4:
                if parts[3] == "regen":
                    await state.set_state(SessionFlowStates.ending_regen)
                    await state.update_data(session_id=sid, **fsm_data)
                await handle_ending_callback(
                    callback,
                    session,
                    row,
                    sid=sid,
                    uid=uid,
                    lang=lang,
                    action=parts[3],
                    fsm_data=fsm_data,
                )
                await state.update_data(session_id=sid, **fsm_data)
                return
            if parts[2] == "tribal" and len(parts) == 4:
                needs_feedback = await handle_tribal_callback(
                    callback,
                    session,
                    row,
                    sid=sid,
                    uid=uid,
                    lang=lang,
                    yes=parts[3] == "yes",
                )
                if needs_feedback:
                    await state.set_state(SessionFlowStates.tribal_feedback)
                    await state.update_data(session_id=sid)
                return
            if parts[2] == "fin" and len(parts) == 4:
                await handle_finalize_callback(
                    callback,
                    session,
                    row,
                    sid=sid,
                    uid=uid,
                    lang=lang,
                    action=parts[3],
                    fsm_data=fsm_data,
                )
                return
            if parts[2] == "pub" and len(parts) == 4:
                await handle_publish_callback(
                    callback,
                    session,
                    row,
                    sid=sid,
                    uid=uid,
                    lang=lang,
                    action=parts[3],
                    fsm_data=fsm_data,
                    bot=callback.bot,
                )
                await state.update_data(**fsm_data)
                return
            if parts[2] == "pubdest" and len(parts) == 4:
                await handle_publish_dest_toggle(
                    callback,
                    session,
                    row,
                    sid=sid,
                    uid=uid,
                    lang=lang,
                    provider=parts[3],
                    fsm_data=fsm_data,
                )
                await state.update_data(**fsm_data)
                return
            if parts[2] == "pubretry" and len(parts) == 4:
                await handle_publish_retry(
                    callback,
                    session,
                    row,
                    sid=sid,
                    uid=uid,
                    lang=lang,
                    provider=parts[3],
                    bot=callback.bot,
                )
                return

        if parts[2] == "pick" and len(parts) == 5:
            round_no = int(parts[3])
            idx = int(parts[4])
            dr = await get_latest_draft_round(session, sid)
            if dr is None or dr.round_no != round_no:
                await callback.answer()
                return
            opts = parse_options(dr)
            await select_draft_option(session, dr, idx)
            row.final_draft_text = opts[idx]
            await session.commit()
            await set_session_state(session, row, "awaiting_follow_up")
            await callback.message.answer(  # type: ignore[union-attr]
                t("session_follow_up", lang),
                reply_markup=follow_up_keyboard(sid, lang),
            )
            await callback.answer()
            return

        if parts[2] == "custom" and len(parts) == 4:
            await set_session_state(session, row, "awaiting_custom_draft")
            await state.set_state(SessionCustomStates.draft_custom)
            await state.update_data(session_id=sid)
            await callback.message.answer(t("onboarding_custom_prompt", lang))  # type: ignore[union-attr]
            await callback.answer()
            return

        if parts[2] == "fu" and len(parts) == 4:
            action = parts[3]
            dr = await get_latest_draft_round(session, sid)
            if dr is None or dr.selected_index is None:
                await callback.answer()
                return
            options = parse_options(dr)
            selected = options[dr.selected_index]
            profile_summary = await format_profile_summary(session, uid, lang)
            profile, _ = await current_prompt_context(
                session,
                telegram_user_id=uid,
                locale=lang,
                fallback_summary=profile_summary,
            )
            input_text = await aggregate_input_text(session, sid)
            orch = DraftOrchestrator()

            if action == "new":
                new_opts = await orch.generate_follow_up_round(
                    profile_summary=profile,
                    content_language=lang,
                    input_text=input_text,
                    prior_options=options,
                    selected_index=dr.selected_index,
                    feedback=None,
                )
                rnd = await next_round_no(session, sid)
                await save_draft_round(session, sid, round_no=rnd, options=new_opts)
                await set_session_state(session, row, "awaiting_draft_choice")
                await callback.message.answer(  # type: ignore[union-attr]
                    t("session_pick_draft", lang),
                    reply_markup=draft_options_keyboard(sid, rnd, new_opts, lang),
                )
            elif action == "refine":
                new_opts = await orch.refine_selected(
                    profile_summary=profile,
                    content_language=lang,
                    input_text=input_text,
                    selected_text=selected,
                    feedback=None,
                )
                rnd = await next_round_no(session, sid)
                await save_draft_round(
                    session, sid, round_no=rnd, options=new_opts, is_refinement=True
                )
                await set_session_state(session, row, "awaiting_draft_choice")
                await callback.message.answer(  # type: ignore[union-attr]
                    t("session_pick_draft", lang),
                    reply_markup=draft_options_keyboard(sid, rnd, new_opts, lang),
                )
            elif action == "confirm":
                text = row.final_draft_text or selected
                await set_final_draft(session, row, text)
                await _after_confirm_callback(callback, session, row, lang)
            await callback.answer()
            return

        if parts[2] == "publish":
            text = row.final_draft_text
            if not text:
                await callback.answer(t("session_no_final_draft", lang), show_alert=True)
                return
            if row.cover_generation and not row.cover_storage_ref:
                cover_ref = await CoverStep().generate(draft_text=text, session_id=sid)
                row.cover_storage_ref = cover_ref
                await session.commit()
            results = await PublishOrchestrator(bot=callback.bot).publish_session(
                session,
                session_id=sid,
                telegram_user_id=uid,
                draft_text=text,
            )
            row.state = "published"
            row.is_active = False
            await session.commit()
            lines = "\n".join(
                f"• <b>{r.provider}</b>: {r.url or r.error or '—'}" for r in results
            )
            await callback.message.answer(  # type: ignore[union-attr]
                t("session_published", lang).format(links=lines)
            )
            await callback.answer()
            return

    await callback.answer()


async def _after_confirm(message: Message, session, row, lang: str) -> None:
    if row.cover_generation:
        cover_ref = await CoverStep().generate(
            draft_text=row.final_draft_text or "", session_id=row.id
        )
        row.cover_storage_ref = cover_ref
        await session.commit()
        await message.answer(t("session_cover_ready", lang).format(ref=cover_ref))
    await set_session_state(session, row, "awaiting_publish")
    await message.answer(
        t("session_ready_publish", lang),
        reply_markup=publish_keyboard(row.id, lang),
    )


async def _after_confirm_callback(callback: CallbackQuery, session, row, lang: str) -> None:
    if row.cover_generation:
        cover_ref = await CoverStep().generate(
            draft_text=row.final_draft_text or "", session_id=row.id
        )
        row.cover_storage_ref = cover_ref
        await session.commit()
        await callback.message.answer(  # type: ignore[union-attr]
            t("session_cover_ready", lang).format(ref=cover_ref)
        )
    await set_session_state(session, row, "awaiting_publish")
    await callback.message.answer(  # type: ignore[union-attr]
        t("session_ready_publish", lang),
        reply_markup=publish_keyboard(row.id, lang),
    )
