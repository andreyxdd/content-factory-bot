from __future__ import annotations

import re

import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from content_factory_bot.db.session import session_scope
from content_factory_bot.handlers.providers_screen import send_providers_screen
from content_factory_bot.middleware.locale import UI_LANG_KEY
from content_factory_bot.services.creators import ensure_creator
from content_factory_bot.services.onboarding_engine import (
    build_s2_summary,
    build_style_card,
    build_system_prompt,
    build_tribal_block,
    build_values_block,
    editable_fields_for_confirm,
    extract_first_url,
)
from content_factory_bot.services.profile import (
    apply_creator_preferences,
    get_profile_answers_map,
    mark_profile_ready,
    save_answer,
    save_profile_artifacts,
)

router = Router(name="onboarding")


class OnboardingStates(StatesGroup):
    in_progress = State()


TEXT_STEP_BY_KEY = {
    "s2_about": "s2_about",
    "s2_audience": "s2_audience",
    "s2_platforms": "s2_platforms",
    "s2_reader_feel": "s2_reader_feel",
    "s2_avoid_topics": "s2_avoid_topics",
    "s4_beliefs": "s4_beliefs",
    "s4_contradictions": "s4_contradictions",
    "s4_boundaries": "s4_boundaries",
    "s4_evolution": "s4_evolution",
    "s5_reader_phrase": "s5_reader_phrase",
    "s5_voice_betrayal": "s5_voice_betrayal",
}

RESUME_STEP_ORDER = (
    ("s2_about", "s2_about"),
    ("s2_audience", "s2_audience"),
    ("s2_platforms", "s2_platforms"),
    ("s2_goals", "s2_goals"),
    ("s2_reader_feel", "s2_reader_feel"),
    ("s2_avoid_topics", "s2_avoid_topics"),
    ("s4_beliefs", "s4_beliefs"),
    ("s4_contradictions", "s4_contradictions"),
    ("s4_boundaries", "s4_boundaries"),
    ("s4_evolution", "s4_evolution"),
    ("s5_reader_phrase", "s5_reader_phrase"),
    ("s5_voice_betrayal", "s5_voice_betrayal"),
    ("web_research", "toggle_research"),
    ("review_agent", "toggle_review"),
)


def _lang(data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


def _yes_set(lang: str) -> set[str]:
    return {"да", "yes", "y", "ok", "готов", "готова"} if lang == "ru" else {"yes", "y", "ok", "ready"}


def _nav_row(lang: str, *, include_back: bool = True) -> list[InlineKeyboardButton]:
    back = "⬅️ Назад" if lang == "ru" else "⬅️ Back"
    cancel = "🛑 Отмена" if lang == "ru" else "🛑 Cancel"
    help_text = "❓ Помощь" if lang == "ru" else "❓ Help"
    row = []
    if include_back:
        row.append(InlineKeyboardButton(text=back, callback_data="onb:nav:back"))
    row.append(InlineKeyboardButton(text=cancel, callback_data="onb:nav:cancel"))
    row.append(InlineKeyboardButton(text=help_text, callback_data="onb:nav:help"))
    return row


def _kb(
    rows: list[list[InlineKeyboardButton]],
    lang: str,
    *,
    include_back: bool = True,
) -> InlineKeyboardMarkup:
    rows = list(rows)
    rows.append(_nav_row(lang, include_back=include_back))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _question_text(step: str, lang: str) -> str:
    if lang == "ru":
        prompts = {
            "s1_ready": "Привет. За 20 минут пройдем 8 шагов и соберем System Prompt в твоем голосе. Готов начать?",
            "s2_about": "Расскажи в 1-2 предложениях кто ты и чем занимаешься.",
            "s2_audience": "Кому ты пишешь? Опиши конкретного человека: возраст, занятие, боль.",
            "s2_platforms": "Где публикуешься или планируешь публиковаться? Назови все и основную платформу.",
            "s2_reader_feel": "Что должен почувствовать читатель после поста?",
            "s2_avoid_topics": "Каких тем или форматов ты точно избегаешь?",
            "s3_samples": "Скинь 3-5 любимых постов: свои, чужие или микс. Можешь отправлять текст, форвард или ссылку.",
            "s4_intro": "Стиль — половина голоса. Вторая половина — что у тебя в голове. 4 быстрых вопроса.",
            "s4_beliefs": "Назови 2-3 убеждения в твоей сфере, которые ты считаешь верными, а мейнстрим — нет.",
            "s4_contradictions": "Какие внутренние противоречия ты иногда проговариваешь вслух?",
            "s4_boundaries": "О чем ты не пишешь публично, даже если есть мысли?",
            "s4_evolution": "Как изменились твои взгляды за последние 1-2 года?",
            "s5_intro": "Финальный смысловой слой. Два коротких вопроса.",
            "s5_reader_phrase": "Какую одну фразу сказал бы идеальный читатель после твоего поста?",
            "s5_voice_betrayal": "Какой пост ты не назвал бы своим, даже если он вирусный?",
            "toggle_warning": (
                "Внимание: включение web_research и review_agent может увеличить расход AI-токенов и стоимость. "
                "Можешь изменить это позже в /profile или /settings."
            ),
            "toggle_research": "Включить web research по умолчанию для новых сессий?",
            "toggle_review": "Включить review-agent по умолчанию для черновиков?",
        }
    else:
        prompts = {
            "s1_ready": "Hi. In ~20 minutes we will pass 8 steps and produce a System Prompt in your voice. Ready to start?",
            "s2_about": "In 1-2 sentences, who are you and what do you do?",
            "s2_audience": "Who do you write for? Describe one concrete person: age, role, pain.",
            "s2_platforms": "Where do you publish or plan to publish? List all and mark the main one.",
            "s2_reader_feel": "What should the reader feel after your post?",
            "s2_avoid_topics": "What topics or formats do you explicitly avoid?",
            "s3_samples": "Send 3-5 favorite posts: yours, others, or mix. Text, forward, or link is fine.",
            "s4_intro": "Style is half of voice. The other half is what is in your head. 4 quick questions.",
            "s4_beliefs": "Name 2-3 contrarian beliefs in your domain.",
            "s4_contradictions": "What inner contradictions do you sometimes say out loud?",
            "s4_boundaries": "What do you avoid discussing publicly?",
            "s4_evolution": "How did your view evolve in the last 1-2 years?",
            "s5_intro": "Final semantic layer. Two short questions.",
            "s5_reader_phrase": "What single phrase should the ideal reader say after reading your post?",
            "s5_voice_betrayal": "What post would you call voice betrayal even if it went viral?",
            "toggle_warning": (
                "Warning: enabling web_research and review_agent may increase AI token usage and cost. "
                "You can switch both later in /profile or /settings."
            ),
            "toggle_research": "Enable web research by default for new sessions?",
            "toggle_review": "Enable review-agent by default for drafts?",
        }
    return prompts[step]


def _help_text(step: str, lang: str) -> str:
    key = step if step in {
        "s1_ready",
        "s2_about",
        "s2_audience",
        "s2_platforms",
        "s2_goals",
        "s2_reader_feel",
        "s2_avoid_topics",
        "s2_confirm",
        "s3_samples",
        "s3_confirm",
        "s4_beliefs",
        "s4_contradictions",
        "s4_boundaries",
        "s4_evolution",
        "s4_confirm",
        "s5_reader_phrase",
        "s5_voice_betrayal",
        "s6_confirm",
        "toggle_research",
        "toggle_review",
    } else "fallback"
    if lang == "ru":
        texts = {
            "s1_ready": "Коротко: онбординг собирает твой голос и настройки. Нажми «Продолжить», чтобы начать.",
            "s2_about": "Кто ты и чем занимаешься сейчас. Пример: «Я product engineer, строю AI-инструменты для авторов».",
            "s2_audience": "Опиши одного типичного читателя: роль, уровень, боль. Пример: «PM 28 лет, тонет в хаосе задач».",
            "s2_platforms": "Где публикуешься и что главное. Пример: «Telegram и LinkedIn, основной канал — Telegram».",
            "s2_goals": "Зачем тебе контент сейчас. Выбери несколько пунктов и нажми «Готово».",
            "s2_reader_feel": "Какое чувство должен получить читатель. Пример: «Ясность, спокойствие и импульс действовать».",
            "s2_avoid_topics": "Темы и форматы, которые ты не публикуешь. Пример: «Политика, токсичный хейт, кликбейт».",
            "s2_confirm": "Проверь карточку. Можно: подтвердить, продолжить дальше, выбрать поле для правки или прислать правку текстом.",
            "s3_samples": "Пришли 3-5 образцов: текст, форвард или ссылка. Когда хватит — «Анализировать образцы» или «Пропустить пока».",
            "s3_confirm": "Это черновой style card по образцам. Если не похоже на тебя, напиши корректировку.",
            "s4_beliefs": (
                "2-3 убеждения, с которыми большинство в твоей сфере не согласится.\n\n"
                "Пример (софт):\n"
                "«MVP должен быть грубее и выходить за 3 дня».\n"
                "«Большинству команд нужно меньше микросервисов, а не больше».\n"
                "«Меньше сеньоров + сильный процесс лучше, чем раздутый штат»."
            ),
            "s4_contradictions": "Внутренние противоречия, которые ты признаешь вслух. Пример: «Я за баланс, но отвечаю в полночь».",
            "s4_boundaries": "О чем принципиально не пишешь публично. Пример: «Семейные детали, чужие доходы, приватные конфликты».",
            "s4_evolution": "Как твой взгляд изменился за 1-2 года. Пример: «Раньше гнался за охватом, теперь за качеством диалога».",
            "s4_confirm": "Проверь блок ценностей. Если формулировка не твоя, поправь полем или текстом.",
            "s5_reader_phrase": "Одна фраза, которую должен сказать идеальный читатель после поста. Пример: «Это прямо про меня».",
            "s5_voice_betrayal": "Какой пост был бы «не твоим голосом», даже если вирусный. Пример: «Манипулятивный хайп без пользы».",
            "s6_confirm": "Это собранный system prompt. Проверь и продолжай к финальным переключателям.",
            "toggle_research": "Включает веб-исследование в новых сессиях по умолчанию. Можно менять позже в /profile или /settings.",
            "toggle_review": "Включает review-agent для черновиков по умолчанию. Можно менять позже.",
            "fallback": "Правила: один вопрос за раз. Можно нажимать кнопки или отвечать текстом. «Назад» возвращает к прошлому шагу.",
        }
    else:
        texts = {
            "s1_ready": "Short version: onboarding captures your voice and defaults. Press Continue to start.",
            "s2_about": "Who you are and what you do now. Example: \"I am a product engineer building AI tools for creators.\"",
            "s2_audience": "Describe one concrete reader: role, level, pain. Example: \"28-year-old PM drowning in task chaos.\"",
            "s2_platforms": "Where you publish and which one is primary. Example: \"Telegram and LinkedIn; main channel is Telegram.\"",
            "s2_goals": "Why you need content now. Select multiple options, then press Done.",
            "s2_reader_feel": "What feeling the reader should leave with. Example: \"Clarity, relief, and motivation to act.\"",
            "s2_avoid_topics": "Topics/formats you never publish. Example: \"Politics, rage-bait, manipulative clickbait.\"",
            "s2_confirm": "Review your profile card. You can confirm, continue, edit a field, or send free-text correction.",
            "s3_samples": "Send 3-5 samples: text, forward, or links. Then press Analyze samples or Skip for now.",
            "s3_confirm": "This is a draft style card from your samples. If it misses your voice, send corrections.",
            "s4_beliefs": (
                "2-3 opinions you hold that most people in your field disagree with.\n\n"
                "Example (software):\n"
                "\"MVPs should be uglier and ship in 3 days.\"\n"
                "\"Most teams should use fewer microservices, not more.\"\n"
                "\"Hiring fewer seniors + better process beats big headcount.\""
            ),
            "s4_contradictions": "Beliefs or behaviors that conflict, but you admit openly. Example: \"I preach balance but reply at midnight.\"",
            "s4_boundaries": "What you refuse to discuss publicly. Example: \"Family details, private conflicts, client secrets.\"",
            "s4_evolution": "How your view changed in 1-2 years. Example: \"I used to chase reach; now I optimize for trust.\"",
            "s4_confirm": "Review your values block. If wording is off, edit fields or send text corrections.",
            "s5_reader_phrase": "One line your ideal reader should say after a post. Example: \"This finally put my thoughts in order.\"",
            "s5_voice_betrayal": "What kind of post would betray your voice, even if viral. Example: \"Hypey manipulation with no substance.\"",
            "s6_confirm": "This is your assembled system prompt. Review it, then continue to final toggles.",
            "toggle_research": "Enables web research by default in new sessions. You can change this later in /profile or /settings.",
            "toggle_review": "Enables review-agent by default for drafts. You can change this later.",
            "fallback": "Rules: one question at a time. Use buttons or text replies. Back returns to the previous step.",
        }
    return texts[key]


def _goal_kb(lang: str, selected: set[str]) -> InlineKeyboardMarkup:
    labels = (
        [("a", "продавать продукт/услугу"), ("b", "собирать комьюнити"), ("c", "строить личный бренд"), ("d", "партнеры и нетворк"), ("e", "другое")]
        if lang == "ru"
        else [("a", "sell product/service"), ("b", "build community"), ("c", "build personal brand"), ("d", "find partners/network"), ("e", "other")]
    )
    rows: list[list[InlineKeyboardButton]] = []
    for key, label in labels:
        mark = "✅ " if key in selected else ""
        rows.append([InlineKeyboardButton(text=f"{mark}{key}) {label}", callback_data=f"onb:goal:{key}")])
    done_text = "Готово" if lang == "ru" else "Done"
    rows.append([InlineKeyboardButton(text=done_text, callback_data="onb:goal:done")])
    return _kb(rows, lang)


def _binary_kb(prefix: str, lang: str, *, include_back: bool = True) -> InlineKeyboardMarkup:
    yes = "Да" if lang == "ru" else "Yes"
    no = "Нет" if lang == "ru" else "No"
    return _kb(
        [
            [InlineKeyboardButton(text=yes, callback_data=f"{prefix}:yes")],
            [InlineKeyboardButton(text=no, callback_data=f"{prefix}:no")],
        ],
        lang,
        include_back=include_back,
    )


def _ready_kb(lang: str) -> InlineKeyboardMarkup:
    continue_label = "Продолжить" if lang == "ru" else "Continue"
    return _kb(
        [[InlineKeyboardButton(text=continue_label, callback_data="onb:ready:yes")]],
        lang,
        include_back=False,
    )


def _confirm_kb(kind: str, lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        ok, edit, next_text = "Похоже", "Редактировать поле", "Дальше"
    else:
        ok, edit, next_text = "Looks right", "Edit field", "Continue"
    return _kb(
        [
            [InlineKeyboardButton(text=ok, callback_data=f"onb:{kind}:ok")],
            [InlineKeyboardButton(text=edit, callback_data=f"onb:{kind}:edit")],
            [InlineKeyboardButton(text=next_text, callback_data=f"onb:{kind}:next")],
        ],
        lang,
    )


def _confirm_edit_fork_kb(kind: str, lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        edit_label = "Редактировать отвеченные поля"
        continue_label = "Продолжить с оставшимися вопросами"
    else:
        edit_label = "Edit answered fields"
        continue_label = "Continue with additional questions"
    return _kb(
        [
            [InlineKeyboardButton(text=edit_label, callback_data=f"onb:{kind}:edit_fields")],
            [InlineKeyboardButton(text=continue_label, callback_data=f"onb:{kind}:continue_questions")],
        ],
        lang,
    )


def _edit_field_kb(lang: str, confirm_step: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f.label(lang), callback_data=f"onb:edit:{f.key}")]
        for f in editable_fields_for_confirm(confirm_step)
    ]
    return _kb(rows, lang)


async def _advance_from_confirm(message: Message, state: FSMContext, lang: str, uid: int, confirm_step: str, fsm: dict) -> None:
    next_step = _next_step(confirm_step)
    if next_step is None:
        return
    if next_step == "s4_beliefs":
        await message.answer(_question_text("s4_intro", lang))
    if next_step == "s5_reader_phrase":
        await message.answer(_question_text("s5_intro", lang))
    if next_step == "done":
        await _finish_onboarding(message, state, uid, lang)
        return
    await state.update_data(current_step=next_step, flow_stack=list(fsm.get("flow_stack", [])) + [confirm_step])
    if next_step in {"s4_confirm", "s6_confirm"}:
        await _show_confirm_blocks(message, state, next_step, lang)
    else:
        await _send_prompt(message, state, lang, next_step)


async def _return_to_confirm(message: Message, state: FSMContext, lang: str, confirm_step: str) -> None:
    fsm = await state.get_data()
    answers = fsm.get("answers", {})
    updates: dict[str, str | None] = {
        "current_step": confirm_step,
        "pending_edit_key": None,
        "pending_edit_confirm_step": None,
    }
    if confirm_step == "s4_confirm":
        updates["values_block_text"] = build_values_block(answers, lang)
    if confirm_step == "s6_confirm":
        style = fsm.get("style_card_text", build_style_card([], lang))
        values = build_values_block(answers, lang)
        tribal = build_tribal_block(answers, lang)
        updates["values_block_text"] = values
        updates["tribal_block_text"] = tribal
        updates["system_prompt_text"] = build_system_prompt(answers, style, values, tribal)
    await state.update_data(**updates)
    await _show_confirm_blocks(message, state, confirm_step, lang)


async def _send_prompt(target: Message, state: FSMContext, lang: str, step: str) -> None:
    await state.update_data(current_step=step)
    if step == "s2_goals":
        selected = set((await state.get_data()).get("goal_selected", []))
        text = (
            "Зачем тебе контент? Можно выбрать несколько и нажать «Готово»."
            if lang == "ru"
            else "Why do you need content now? You can select multiple and press Done."
        )
        await target.answer(text, reply_markup=_goal_kb(lang, selected))
        return
    if step == "s1_ready":
        await target.answer(
            _question_text(step, lang),
            reply_markup=_ready_kb(lang),
        )
        return
    if step == "s3_samples":
        analyze = "Анализировать образцы" if lang == "ru" else "Analyze samples"
        skip = "Пропустить пока" if lang == "ru" else "Skip for now"
        await target.answer(
            _question_text(step, lang),
            reply_markup=_kb(
                [
                    [InlineKeyboardButton(text=analyze, callback_data="onb:sample:analyze")],
                    [InlineKeyboardButton(text=skip, callback_data="onb:sample:skip")],
                ],
                lang,
            ),
        )
        return
    if step == "toggle_research":
        await target.answer(_question_text("toggle_warning", lang))
        await target.answer(_question_text(step, lang), reply_markup=_binary_kb("onb:toggle:web", lang))
        return
    if step == "toggle_review":
        await target.answer(_question_text(step, lang), reply_markup=_binary_kb("onb:toggle:review", lang))
        return
    await target.answer(_question_text(step, lang), reply_markup=_kb([], lang))


def _next_step(step: str) -> str | None:
    flow = [
        "s1_ready",
        "s2_about",
        "s2_audience",
        "s2_platforms",
        "s2_goals",
        "s2_reader_feel",
        "s2_avoid_topics",
        "s2_confirm",
        "s3_samples",
        "s3_confirm",
        "s4_beliefs",
        "s4_contradictions",
        "s4_boundaries",
        "s4_evolution",
        "s4_confirm",
        "s5_reader_phrase",
        "s5_voice_betrayal",
        "s6_confirm",
        "toggle_research",
        "toggle_review",
        "done",
    ]
    idx = flow.index(step)
    if idx + 1 >= len(flow):
        return None
    return flow[idx + 1]


def _save_text_key(step: str) -> str | None:
    return TEXT_STEP_BY_KEY.get(step)


def _resume_step_from_answers(answers: dict[str, str]) -> str:
    answered = set(answers.keys())
    for key, step in RESUME_STEP_ORDER:
        if key not in answered:
            return step
    return "s6_confirm"


def _goal_selection_from_answer(raw: str | None) -> list[str]:
    if not raw:
        return []
    selected: list[str] = []
    for token in re.findall(r"\b([abcde])\b", raw.lower()):
        if token not in selected:
            selected.append(token)
    return selected


async def _persist_answer(uid: int, key: str, value: str, option_index: int | None = None) -> None:
    async with session_scope() as session:
        await save_answer(
            session,
            uid,
            key,
            value,
            option_index=option_index,
            is_custom=option_index is None,
        )


async def _show_confirm_blocks(message: Message, state: FSMContext, step: str, lang: str) -> None:
    fsm = await state.get_data()
    answers = fsm.get("answers", {})
    if step == "s2_confirm":
        text = build_s2_summary(answers, lang)
        help_text = (
            "Похоже на тебя? Нажми «Похоже» или «Дальше». Для точечной правки — «Редактировать поле» или напиши правку сообщением."
            if lang == "ru"
            else "Does this fit you? Press Looks right or Continue. For targeted changes use Edit field or send free-text correction."
        )
    elif step == "s3_confirm":
        text = f"ТВОЙ STYLE CARD\n\n{fsm.get('style_card_text', '')}" if lang == "ru" else f"YOUR STYLE CARD\n\n{fsm.get('style_card_text', '')}"
        help_text = (
            "Похоже на тебя? Можно идти дальше или прислать правки текстом."
            if lang == "ru"
            else "Does this match you? Continue or send correction text."
        )
    elif step == "s4_confirm":
        text = fsm.get("values_block_text", "")
        help_text = "Это про тебя?" if lang == "ru" else "Is this about you?"
    else:
        text = fsm.get("system_prompt_text", "")
        help_text = (
            "Готово. Сохранить и переходить к настройкам?"
            if lang == "ru"
            else "Done. Save and move to settings toggles?"
        )
    await message.answer(text)
    await message.answer(help_text, reply_markup=_confirm_kb(step, lang))


async def _finish_onboarding(message: Message, state: FSMContext, uid: int, lang: str) -> None:
    fsm = await state.get_data()
    async with session_scope() as session:
        await apply_creator_preferences(session, uid)
        await save_profile_artifacts(
            session,
            uid,
            style_card_text=fsm.get("style_card_text", ""),
            values_block_text=fsm.get("values_block_text", ""),
            tribal_block_text=fsm.get("tribal_block_text", ""),
            system_prompt_text=fsm.get("system_prompt_text", ""),
        )
        await mark_profile_ready(session, uid)
    done_text = (
        "Онбординг завершен. Профиль готов. Дальше подключи каналы и переходи в /new."
        if lang == "ru"
        else "Onboarding complete. Profile is ready. Connect channels and continue in /new."
    )
    await message.answer(done_text)
    await send_providers_screen(message, lang=lang, uid=uid, show_skip=True)
    await state.clear()


async def _fetch_link_sample(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                return None
            html = response.text
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\\s+", " ", text).strip()
            if len(text) < 120:
                return None
            return text[:4000]
    except Exception:
        return None


@router.message(Command("onboarding"))
async def cmd_onboarding(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user:
        return
    uid = message.from_user.id
    lang = _lang(data)
    async with session_scope() as session:
        await ensure_creator(
            session,
            telegram_user_id=uid,
            language_code=message.from_user.language_code,
        )
    await state.set_state(OnboardingStates.in_progress)
    fsm = await state.get_data()
    step = fsm.get("current_step")
    if step:
        await _send_prompt(message, state, lang, step)
        return
    async with session_scope() as session:
        answers = await get_profile_answers_map(session, uid)
    if answers:
        resume_step = _resume_step_from_answers(answers)
        await state.update_data(
            current_step=resume_step,
            flow_stack=[],
            answers=answers,
            goal_selected=_goal_selection_from_answer(answers.get("s2_goals")),
            samples=[],
            pending_edit_key=None,
            pending_edit_confirm_step=None,
        )
        await _send_prompt(message, state, lang, resume_step)
        return
    await state.update_data(
        current_step="s1_ready",
        flow_stack=[],
        answers={},
        goal_selected=[],
        samples=[],
        pending_edit_key=None,
        pending_edit_confirm_step=None,
    )
    await _send_prompt(message, state, lang, "s1_ready")


@router.callback_query(OnboardingStates.in_progress, F.data.startswith("onb:"))
async def on_onboarding_callback(callback: CallbackQuery, state: FSMContext, **data) -> None:
    if not callback.from_user or not callback.data or not callback.message:
        return
    uid = callback.from_user.id
    lang = _lang(data)
    fsm = await state.get_data()
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return

    if parts[1] == "nav":
        action = parts[2]
        if action == "cancel":
            await state.clear()
            await callback.message.answer("Онбординг отменен." if lang == "ru" else "Onboarding cancelled.")
            await callback.answer()
            return
        if action == "help":
            text = _help_text(fsm.get("current_step", "fallback"), lang)
            await callback.message.answer(text)
            await callback.answer()
            return
        if action == "back":
            stack = list(fsm.get("flow_stack", []))
            if stack:
                prev = stack.pop()
                await state.update_data(flow_stack=stack, current_step=prev)
                await _send_prompt(callback.message, state, lang, prev)
            await callback.answer()
            return

    if parts[1] == "ready":
        if parts[2] == "yes":
            await state.update_data(flow_stack=["s1_ready"], current_step="s2_about")
            await _send_prompt(callback.message, state, lang, "s2_about")
        else:
            await callback.message.answer("Напиши «да», когда будешь готов." if lang == "ru" else "Send 'yes' when ready.")
        await callback.answer()
        return

    if parts[1] == "goal":
        selected = set(fsm.get("goal_selected", []))
        key = parts[2]
        if key == "done":
            if not selected:
                await callback.answer("Выбери хотя бы 1 цель." if lang == "ru" else "Pick at least one goal.", show_alert=True)
                return
            goal_text = ", ".join(sorted(selected))
            answers = dict(fsm.get("answers", {}))
            answers["s2_goals"] = goal_text
            await state.update_data(answers=answers)
            await _persist_answer(uid, "s2_goals", goal_text, None)
            pending_edit = fsm.get("pending_edit_key")
            pending_confirm = fsm.get("pending_edit_confirm_step")
            if pending_edit == "s2_goals" and pending_confirm:
                await _return_to_confirm(callback.message, state, lang, pending_confirm)
                await callback.answer()
                return
            if "e" in selected:
                await callback.message.answer("Опиши «другое» коротко." if lang == "ru" else "Describe your 'other' goal briefly.")
                await callback.answer()
                return
            await state.update_data(flow_stack=list(fsm.get("flow_stack", [])) + ["s2_goals"], current_step="s2_reader_feel")
            await _send_prompt(callback.message, state, lang, "s2_reader_feel")
            await callback.answer()
            return
        if key in selected:
            selected.remove(key)
        else:
            selected.add(key)
        await state.update_data(goal_selected=sorted(selected))
        await callback.message.edit_reply_markup(reply_markup=_goal_kb(lang, selected))
        await callback.answer()
        return

    if parts[1] == "sample":
        if parts[2] == "skip":
            style_card = build_style_card([], lang)
            await state.update_data(style_card_text=style_card, current_step="s3_confirm", flow_stack=list(fsm.get("flow_stack", [])) + ["s3_samples"])
            await _show_confirm_blocks(callback.message, state, "s3_confirm", lang)
            await callback.answer()
            return
        if parts[2] == "analyze":
            samples = list(fsm.get("samples", []))
            style_card = build_style_card(samples, lang)
            await state.update_data(style_card_text=style_card, current_step="s3_confirm", flow_stack=list(fsm.get("flow_stack", [])) + ["s3_samples"])
            await _show_confirm_blocks(callback.message, state, "s3_confirm", lang)
            await callback.answer()
            return

    if parts[1] in {"s2_confirm", "s3_confirm", "s4_confirm", "s6_confirm"}:
        action = parts[2]
        if action == "edit":
            if parts[1] in {"s2_confirm", "s3_confirm", "s4_confirm"}:
                await callback.message.answer(
                    "Мы еще не прошли все вопросы профиля. Можешь отредактировать уже отвеченные поля или продолжить с оставшимися."
                    if lang == "ru"
                    else "We have not asked all profile questions yet. You can edit answered fields now or continue with additional questions.",
                    reply_markup=_confirm_edit_fork_kb(parts[1], lang),
                )
            else:
                await callback.message.answer(
                    "Выбери поле для правки или отправь корректировку текстом."
                    if lang == "ru"
                    else "Choose a field to edit or send correction text.",
                    reply_markup=_edit_field_kb(lang, parts[1]),
                )
            await callback.answer()
            return
        if action == "edit_fields":
            await state.update_data(pending_edit_confirm_step=parts[1])
            await callback.message.answer(
                "Выбери поле для правки или отправь корректировку текстом."
                if lang == "ru"
                else "Choose a field to edit or send correction text.",
                reply_markup=_edit_field_kb(lang, parts[1]),
            )
            await callback.answer()
            return
        if action == "continue_questions":
            await _advance_from_confirm(callback.message, state, lang, uid, parts[1], fsm)
            await callback.answer()
            return
        if action in {"ok", "next"}:
            await _advance_from_confirm(callback.message, state, lang, uid, parts[1], fsm)
            await callback.answer()
            return

    if parts[1] == "edit" and len(parts) == 3:
        edit_key = parts[2]
        confirm_step = fsm.get("pending_edit_confirm_step", "s2_confirm")
        await state.update_data(current_step=edit_key, pending_edit_key=edit_key, pending_edit_confirm_step=confirm_step)
        await _send_prompt(callback.message, state, lang, edit_key)
        await callback.answer()
        return

    if parts[1] == "toggle" and len(parts) == 4:
        toggle_kind = parts[2]
        value = parts[3]
        yes = 0 if value == "yes" else 1
        key = "web_research" if toggle_kind == "web" else "review_agent"
        text = "Yes" if value == "yes" else "No"
        await _persist_answer(uid, key, text, yes)
        if key == "web_research":
            await state.update_data(current_step="toggle_review", flow_stack=list(fsm.get("flow_stack", [])) + ["toggle_research"])
            await _send_prompt(callback.message, state, lang, "toggle_review")
        else:
            await state.update_data(current_step="done")
            await _finish_onboarding(callback.message, state, uid, lang)
        await callback.answer()
        return

    await callback.answer()


@router.message(OnboardingStates.in_progress, F.text, ~F.text.startswith("/"))
async def on_onboarding_text(message: Message, state: FSMContext, **data) -> None:
    if not message.from_user or not message.text:
        return
    lang = _lang(data)
    uid = message.from_user.id
    text = message.text.strip()
    fsm = await state.get_data()
    step = fsm.get("current_step")
    if not step:
        return

    if step == "s1_ready":
        if text.lower() in _yes_set(lang):
            await state.update_data(current_step="s2_about", flow_stack=["s1_ready"])
            await _send_prompt(message, state, lang, "s2_about")
        return

    if step == "s3_samples":
        samples = list(fsm.get("samples", []))
        url = extract_first_url(text)
        if url:
            fetched = await _fetch_link_sample(url)
            if not fetched:
                warn = "Не удалось прочитать ссылку. Вставь текст поста вручную." if lang == "ru" else "Could not fetch link. Paste post text manually."
                await message.answer(warn)
                return
            samples.append(fetched)
        else:
            samples.append(text)
        await state.update_data(samples=samples)
        ack = f"Образец сохранен ({len(samples)})." if lang == "ru" else f"Sample saved ({len(samples)})."
        await message.answer(ack)
        return

    if step == "s2_goals" and "e" in set(fsm.get("goal_selected", [])):
        answers = dict(fsm.get("answers", {}))
        merged = f"{answers.get('s2_goals', '')}; other: {text}".strip("; ")
        answers["s2_goals"] = merged
        await state.update_data(answers=answers)
        await _persist_answer(uid, "s2_goals", merged, None)
        pending_edit = fsm.get("pending_edit_key")
        pending_confirm = fsm.get("pending_edit_confirm_step")
        if pending_edit == "s2_goals" and pending_confirm:
            await _return_to_confirm(message, state, lang, pending_confirm)
            return
        await state.update_data(current_step="s2_reader_feel", flow_stack=list(fsm.get("flow_stack", [])) + ["s2_goals"])
        await _send_prompt(message, state, lang, "s2_reader_feel")
        return

    if step in {"s2_confirm", "s3_confirm", "s4_confirm", "s6_confirm"}:
        await message.answer("Правка сохранена. Можем идти дальше." if lang == "ru" else "Correction saved. We can continue.")
        return

    key = _save_text_key(step)
    if key:
        answers = dict(fsm.get("answers", {}))
        answers[key] = text
        await state.update_data(answers=answers)
        await _persist_answer(uid, key, text, None)
        pending_edit = fsm.get("pending_edit_key")
        if pending_edit:
            confirm_step = fsm.get("pending_edit_confirm_step", "s2_confirm")
            await _return_to_confirm(message, state, lang, confirm_step)
            return
        next_step = _next_step(step)
        if next_step == "s2_confirm":
            await state.update_data(current_step="s2_confirm", flow_stack=list(fsm.get("flow_stack", [])) + [step])
            await _show_confirm_blocks(message, state, "s2_confirm", lang)
            return
        if next_step == "s4_confirm":
            values_block = build_values_block(answers, lang)
            await state.update_data(values_block_text=values_block, current_step="s4_confirm", flow_stack=list(fsm.get("flow_stack", [])) + [step])
            await _show_confirm_blocks(message, state, "s4_confirm", lang)
            return
        if next_step == "s6_confirm":
            style = fsm.get("style_card_text", build_style_card([], lang))
            values = fsm.get("values_block_text", build_values_block(answers, lang))
            tribal = build_tribal_block(answers, lang)
            system_prompt = build_system_prompt(answers, style, values, tribal)
            await state.update_data(
                tribal_block_text=tribal,
                system_prompt_text=system_prompt,
                current_step="s6_confirm",
                flow_stack=list(fsm.get("flow_stack", [])) + [step],
            )
            await _show_confirm_blocks(message, state, "s6_confirm", lang)
            return
        if next_step:
            if next_step == "s4_beliefs":
                await message.answer(_question_text("s4_intro", lang))
            if next_step == "s5_reader_phrase":
                await message.answer(_question_text("s5_intro", lang))
            await state.update_data(current_step=next_step, flow_stack=list(fsm.get("flow_stack", [])) + [step])
            await _send_prompt(message, state, lang, next_step)
