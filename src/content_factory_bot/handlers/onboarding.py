from __future__ import annotations

import json
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
    S2_KEYS,
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
    "s2_occupation": "occupation",
    "s2_voice_tone": "voice_tone",
    "s2_formats": "formats",
    "s2_niche_topics": "niche_topics",
    "s2_signature_themes": "signature_themes",
    "s2_personal_angle": "personal_angle",
    "s2_human_design": "human_design",
    "s2_cadence": "cadence",
    "s2_reader_feel": "s2_reader_feel",
    "s2_avoid_topics": "s2_avoid_topics",
    "s2_anti_markers": "s2_anti_markers",
    "s4_beliefs": "s4_beliefs",
    "s4_contradictions": "s4_contradictions",
    "s4_boundaries": "s4_boundaries",
    "s4_evolution": "s4_evolution",
    "s5_reader_phrase": "s5_reader_phrase",
    "s5_voice_betrayal": "s5_voice_betrayal",
}

RESUME_STEP_ORDER = (
    ("s2_about", "s2_about"),
    ("occupation", "s2_occupation"),
    ("s2_audience", "s2_audience"),
    ("audience", "s2_audience"),
    ("s2_platforms", "s2_platforms"),
    ("voice_tone", "s2_voice_tone"),
    ("formats", "s2_formats"),
    ("niche_topics", "s2_niche_topics"),
    ("s2_goals", "s2_goals"),
    ("content_goals", "s2_goals"),
    ("signature_themes", "s2_signature_themes"),
    ("personal_angle", "s2_personal_angle"),
    ("human_design", "s2_human_design"),
    ("cadence", "s2_cadence"),
    ("s2_reader_feel", "s2_reader_feel"),
    ("s2_avoid_topics", "s2_avoid_topics"),
    ("hard_limits", "s2_avoid_topics"),
    ("s2_anti_markers", "s2_anti_markers"),
    ("s4_beliefs", "s4_beliefs"),
    ("s4_contradictions", "s4_contradictions"),
    ("s4_boundaries", "s4_boundaries"),
    ("s4_evolution", "s4_evolution"),
    ("s5_reader_phrase", "s5_reader_phrase"),
    ("s5_voice_betrayal", "s5_voice_betrayal"),
    ("web_research", "toggle_research"),
    ("review_agent", "toggle_review"),
)

SKIPPABLE_STEPS = {
    "s2_platforms",
    "s2_goals",
    "s2_anti_markers",
    "s3_samples",
    "s4_beliefs",
    "s4_contradictions",
    "s4_boundaries",
    "s4_evolution",
    "s5_reader_phrase",
    "toggle_research",
    "toggle_review",
}

ONBOARDING_FLOW = [
    "s1_ready",
    "s2_about",
    "s2_occupation",
    "s2_audience",
    "s2_platforms",
    "s2_voice_tone",
    "s2_formats",
    "s2_niche_topics",
    "s2_goals",
    "s2_signature_themes",
    "s2_personal_angle",
    "s2_human_design",
    "s2_cadence",
    "s2_reader_feel",
    "s2_avoid_topics",
    "s2_anti_markers",
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
    "s7_handoff",
    "toggle_research",
    "toggle_review",
    "done",
]
FLOW_INDEX = {step: idx for idx, step in enumerate(ONBOARDING_FLOW)}
SAMPLES_DB_KEY = "s3_samples"
STYLE_CARD_DB_KEY = "s3_style_card"

DEFAULT_ANTI_MARKERS_EN = (
    "in conclusion, it is important to note, in today's fast-paced world, unlock your potential"
)
DEFAULT_ANTI_MARKERS_RU = (
    "в заключение, важно отметить, в современном быстро меняющемся мире, раскройте свой потенциал"
)


def _default_anti_markers(lang: str) -> str:
    return DEFAULT_ANTI_MARKERS_RU if lang == "ru" else DEFAULT_ANTI_MARKERS_EN


def _primary_language_value(lang: str) -> tuple[str, int]:
    return ("Русский", 1) if lang == "ru" else ("English", 0)


def _reaction_text(lang: str) -> str:
    return "Принял. Двигаемся дальше." if lang == "ru" else "Got it. Moving to next question."


def _alias_mappings() -> dict[str, str]:
    return {
        "s2_audience": "audience",
        "s2_goals": "content_goals",
        "s2_avoid_topics": "hard_limits",
    }


def _lang(data: dict) -> str:
    return data.get(UI_LANG_KEY, "en")


def _yes_set(lang: str) -> set[str]:
    return {"да", "yes", "y", "ok", "готов", "готова"} if lang == "ru" else {"yes", "y", "ok", "ready"}


def _checkpoint_step(fsm: dict) -> str | None:
    answers = fsm.get("answers", {})
    profile_checkpoint_keys = set(S2_KEYS) | {
        "occupation",
        "voice_tone",
        "formats",
        "niche_topics",
        "signature_themes",
        "personal_angle",
        "human_design",
        "cadence",
    }
    if fsm.get("system_prompt_text"):
        return "s6_confirm"
    if fsm.get("values_block_text"):
        return "s4_confirm"
    if fsm.get("style_card_text"):
        return "s3_confirm"
    if all(key in answers for key in profile_checkpoint_keys):
        return "s2_confirm"
    return None


def _nav_row(lang: str, *, include_back: bool = True, include_skip: bool = False) -> list[InlineKeyboardButton]:
    back = "⬅️ Назад" if lang == "ru" else "⬅️ Back"
    cancel = "⏸️ Пауза" if lang == "ru" else "⏸️ Pause"
    help_text = "❓ Помощь" if lang == "ru" else "❓ Help"
    skip_text = "⏭️ Пропустить" if lang == "ru" else "⏭️ Skip"
    row = []
    if include_back:
        row.append(InlineKeyboardButton(text=back, callback_data="onb:nav:back"))
    row.append(InlineKeyboardButton(text=cancel, callback_data="onb:nav:cancel"))
    row.append(
        InlineKeyboardButton(
            text=skip_text if include_skip else help_text,
            callback_data="onb:nav:skip" if include_skip else "onb:nav:help",
        )
    )
    return row


def _skip_row(lang: str) -> list[InlineKeyboardButton]:
    text = "⏭️ Пропустить" if lang == "ru" else "⏭️ Skip"
    return [InlineKeyboardButton(text=text, callback_data="onb:nav:skip")]


def _kb(
    rows: list[list[InlineKeyboardButton]],
    lang: str,
    *,
    include_back: bool = True,
    include_skip: bool = False,
) -> InlineKeyboardMarkup:
    rows = list(rows)
    rows.append(_nav_row(lang, include_back=include_back, include_skip=include_skip))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _help_row(lang: str) -> list[InlineKeyboardButton]:
    text = "❓ Помощь" if lang == "ru" else "❓ Help"
    return [InlineKeyboardButton(text=text, callback_data="onb:nav:help")]


def _sample_actions_kb(lang: str, *, include_skip: bool) -> InlineKeyboardMarkup:
    analyze = "🧠 Анализировать образцы" if lang == "ru" else "🧠 Analyze samples"
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=analyze, callback_data="onb:sample:analyze")]
    ]
    if include_skip:
        skip = "⏭️ Пропустить пока" if lang == "ru" else "⏭️ Skip for now"
        rows.append([InlineKeyboardButton(text=skip, callback_data="onb:sample:skip")])
    return _kb(rows, lang)


def _s7_handoff_kb(lang: str) -> InlineKeyboardMarkup:
    start = "🚀 Перейти к /new" if lang == "ru" else "🚀 Go to /new"
    skip = "⏭️ Пропустить тест" if lang == "ru" else "⏭️ Skip test"
    return _kb(
        [
            [InlineKeyboardButton(text=start, callback_data="onb:s7:new")],
            [InlineKeyboardButton(text=skip, callback_data="onb:s7:skip")],
        ],
        lang,
    )


def _question_text(step: str, lang: str) -> str:
    if lang == "ru":
        prompts = {
            "s1_ready": "Привет. За 20 минут пройдем 8 шагов и соберем System Prompt в твоем голосе. Готов начать?",
            "s2_about": (
                "Расскажи в 1-2 предложениях кто ты и чем занимаешься.\n"
                "Например: 'Я коуч по выгоранию для founder-ов B2B SaaS, веду\n"
                "индивидуальные программы и групповые ретриты.'"
            ),
            "s2_occupation": "Что лучше всего описывает чем ты занимаешься сейчас?",
            "s2_audience": (
                "Кому ты пишешь? Опиши их одним абзацем - кто, сколько лет, чем\n"
                "заняты, что у них болит. Не 'все люди', а конкретный человек\n"
                "в голове."
            ),
            "s2_platforms": (
                "Где ты публикуешь сейчас или планируешь? Telegram / Instagram /\n"
                "LinkedIn / Threads / блог - назови все. Если есть основная -\n"
                "скажи какая."
            ),
            "s2_voice_tone": "Какой тон тебе ближе в постах?",
            "s2_formats": "Какие форматы ты реально хочешь публиковать?",
            "s2_niche_topics": "Какой у тебя охват тем?",
            "s2_goals": (
                "Зачем тебе контент? Выбери ближайшее (можно несколько):\n"
                "(a) продавать продукт/услугу\n"
                "(b) собирать комьюнити\n"
                "(c) строить личный бренд / экспертизу\n"
                "(d) находить партнёров и нетворк\n"
                "(e) другое - опиши"
            ),
            "s2_reader_feel": (
                "Что должен почувствовать читатель после твоего поста? Например:\n"
                "одни хотят чтобы читатель сказал 'я не один', другие - 'хочу\n"
                "попробовать прямо сейчас', третьи - 'никогда так не думал'.\n"
                "Можно своими словами."
            ),
            "s2_avoid_topics": (
                "Каких тем или форматов ты избегаешь - что точно НЕ хочешь\n"
                "публиковать? (Например: пустая мотивашка, FOMO ради продаж,\n"
                "корпоративщина, политика, глубоко личное.)"
            ),
            "s2_signature_themes": "Что стоит часто вплетать в посты?",
            "s2_personal_angle": "Что делает контент узнаваемо твоим?",
            "s2_human_design": "Используем ли Human Design как линзу в контенте?",
            "s2_cadence": "Какой ритм публикаций реалистичен для тебя?",
            "s2_anti_markers": (
                "АНТИ-МАРКЕРЫ: что никогда не писать дословно?\n"
                f"По умолчанию: {DEFAULT_ANTI_MARKERS_RU}\n"
                "Отправь свой список через запятую или нажми «Пропустить» чтобы оставить дефолт."
            ),
            "s3_samples": (
                "Теперь самое интересное. Скинь мне 3-5 любимых постов.\n"
                "Можно твоих (если уже пишешь). Можно чужих - на которые ты хочешь\n"
                "быть похож. Можно микс. Просто вставь текст в чат."
            ),
            "s4_intro": (
                "Стиль - это половина голоса. Вторая половина - что у тебя\n"
                "в голове. Без этого AI будет писать стилистически похоже на тебя,\n"
                "но содержательно мимо. 4 быстрых вопроса."
            ),
            "s4_beliefs": (
                "Назови 2-3 убеждения в твоей сфере, которые ты считаешь правильными,\n"
                "а большинство в индустрии - нет. Что-то спорное, неудобное, против\n"
                "мейнстрима. Это твои опорные точки."
            ),
            "s4_contradictions": (
                "Какие у тебя есть внутренние противоречия, которые ты иногда\n"
                "проговариваешь вслух? Например: 'Я говорю что отдых важен, а сам\n"
                "работаю по 12 часов.' Противоречия - это глубина, не слабость."
            ),
            "s4_boundaries": (
                "О чём ты не пишешь публично, даже если есть мысли? Где границы?\n"
                "(Личная жизнь, политика, цифры выручки, конкретные клиенты,\n"
                "здоровье - что у тебя?)"
            ),
            "s4_evolution": (
                "Какая у тебя была эволюция взгляда за последние 1-2 года? То, во что\n"
                "ты раньше верил, а теперь нет. Или наоборот. Это сигнализирует\n"
                "аудитории что ты живой человек, а не статуя."
            ),
            "s5_intro": "Финальный смысловой слой. Ответь на 2 коротких вопроса.",
            "s5_reader_phrase": (
                "Закрой глаза и представь идеального читателя. Он только что дочитал\n"
                "твой пост. Какой одну фразу он сказал бы про себя или вслух?\n"
                "('Я не один в этом', 'хочу попробовать завтра', 'никогда так не\n"
                "думал', 'наконец кто-то это сказал', что-то своё.)"
            ),
            "s5_voice_betrayal": (
                "Какой пост ты бы НЕ назвал своим, даже если бы он завирусился\n"
                "на 100k просмотров? Что для тебя - предательство голоса?"
            ),
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
            "s2_about": (
                "In 1-2 sentences, tell me who you are and what you do.\n"
                "For example: ‘I’m a burnout coach for B2B SaaS founders, I run\n"
                "1:1 programs and group retreats.’"
            ),
            "s2_occupation": "What best describes what you do right now?",
            "s2_audience": (
                "Who do you write for? Describe them in one paragraph - who they are, age,\n"
                "what they do, what hurts. Not ‘all people’, but one concrete person\n"
                "in your head."
            ),
            "s2_platforms": (
                "Where do you publish now or plan to publish? Telegram / Instagram /\n"
                "LinkedIn / Threads / blog - list all. If there is a main one -\n"
                "say which."
            ),
            "s2_voice_tone": "What tone fits you best in posts?",
            "s2_formats": "What formats do you actually want to ship?",
            "s2_niche_topics": "How broad are your recurring topics?",
            "s2_goals": (
                "Why do you need content? Pick what fits most (multiple allowed):\n"
                "(a) sell product/service\n"
                "(b) build community\n"
                "(c) build personal brand / authority\n"
                "(d) find partners and network\n"
                "(e) other - describe"
            ),
            "s2_reader_feel": (
                "What should the reader feel after your post? For example:\n"
                "some want the reader to say ‘I’m not alone’, others - ‘I want\n"
                "to try this right now’, others - ‘I never thought of it this way’.\n"
                "Use your own words."
            ),
            "s2_avoid_topics": (
                "What topics or formats do you avoid - what do you definitely NOT want\n"
                "to publish? (For example: empty motivation posts, FOMO for sales,\n"
                "corporate-speak, politics, deeply personal.)"
            ),
            "s2_signature_themes": "What themes should be woven into posts often?",
            "s2_personal_angle": "What makes your content unmistakably yours?",
            "s2_human_design": "Should Human Design be used as a content lens?",
            "s2_cadence": "What posting cadence is realistic for you?",
            "s2_anti_markers": (
                "ANTI-MARKERS: what phrases should never appear verbatim?\n"
                f"Default: {DEFAULT_ANTI_MARKERS_EN}\n"
                "Send your list comma-separated, or press Skip to keep default."
            ),
            "s3_samples": (
                "Now the fun part. Send me 3-5 favorite posts.\n"
                "They can be yours (if you already write). They can be others’ posts - the style you want\n"
                "to sound like. Or a mix. Just paste text into chat."
            ),
            "s4_intro": (
                "Style is half the voice. The other half is what’s in your head.\n"
                "Without this, AI can sound stylistically like you,\n"
                "but miss your substance. 4 quick questions."
            ),
            "s4_beliefs": (
                "Name 2-3 beliefs in your field that you think are right,\n"
                "while most of the industry disagrees. Something controversial, uncomfortable,\n"
                "against mainstream. These are your anchor points."
            ),
            "s4_contradictions": (
                "What internal contradictions do you have that you sometimes\n"
                "say out loud? Example: ‘I say rest matters, but I\n"
                "work 12 hours.’ Contradictions are depth, not weakness."
            ),
            "s4_boundaries": (
                "What do you not write about publicly, even if you have thoughts?\n"
                "Where are your boundaries?\n"
                "(Personal life, politics, revenue numbers, specific clients,\n"
                "health - what are yours?)"
            ),
            "s4_evolution": (
                "What was your view evolution over the last 1-2 years? Something\n"
                "you believed before, but not now. Or vice versa. This signals\n"
                "to the audience that you’re a living human, not a statue."
            ),
            "s5_intro": "Final semantic layer. Answer 2 short questions.",
            "s5_reader_phrase": (
                "Close your eyes and imagine your ideal reader. They just finished\n"
                "your post. What one phrase would they say to themselves or out loud?\n"
                "(‘I’m not alone in this’, ‘I want to try tomorrow’, ‘I never thought\n"
                "about it this way’, ‘finally someone said this’, or your own.)"
            ),
            "s5_voice_betrayal": (
                "What post would you NOT call yours, even if it went viral\n"
                "to 100k views? What is voice betrayal for you?"
            ),
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
        "s2_occupation",
        "s2_audience",
        "s2_platforms",
        "s2_voice_tone",
        "s2_formats",
        "s2_niche_topics",
        "s2_goals",
        "s2_signature_themes",
        "s2_personal_angle",
        "s2_human_design",
        "s2_cadence",
        "s2_reader_feel",
        "s2_avoid_topics",
        "s2_anti_markers",
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
            "s2_occupation": "Роль одним предложением. Пример: «Founder / builder», «Эксперт / практик», «Креатор».",
            "s2_audience": "Опиши одного типичного читателя: роль, уровень, боль. Пример: «PM 28 лет, тонет в хаосе задач».",
            "s2_platforms": "Где публикуешься и что главное. Пример: «Telegram и LinkedIn, основной канал — Telegram».",
            "s2_voice_tone": "Тон голоса. Пример: «Прямо, без воды» или «Тепло, по-человечески».",
            "s2_formats": "Формат публикаций. Пример: «Короткие посты и треды».",
            "s2_niche_topics": "Покрытие тем. Пример: «2-3 связанные темы».",
            "s2_goals": "Зачем тебе контент сейчас. Выбери несколько пунктов и нажми «Готово».",
            "s2_signature_themes": "Что часто вплетать. Пример: «Личные истории + практический how-to».",
            "s2_personal_angle": "Твой уникальный угол. Пример: «Свой фреймворк и мой карьерный путь».",
            "s2_human_design": "Можно написать «нет» или указать тип/роль, если хочешь учитывать это в контенте.",
            "s2_cadence": "Реалистичная частота публикаций. Пример: «Несколько раз в неделю».",
            "s2_reader_feel": "Какое чувство должен получить читатель. Пример: «Ясность, спокойствие и импульс действовать».",
            "s2_avoid_topics": "Темы и форматы, которые ты не публикуешь. Пример: «Политика, токсичный хейт, кликбейт».",
            "s2_anti_markers": (
                "Фразы-штампы, которые нельзя писать дословно. "
                "Можно оставить дефолт кнопкой «Пропустить» или отправить свой список через запятую."
            ),
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
            "toggle_research": (
                "Включает веб-исследование перед черновиками: бот соберёт короткий brief по актуальным трендам и источникам из живого веба. "
                "Можно менять позже в /profile или /settings."
            ),
            "toggle_review": "Включает review-agent для черновиков по умолчанию. Можно менять позже.",
            "fallback": "Правила: один вопрос за раз. Можно нажимать кнопки или отвечать текстом. «Назад» возвращает к прошлому шагу.",
        }
    else:
        texts = {
            "s1_ready": "Short version: onboarding captures your voice and defaults. Press Continue to start.",
            "s2_about": "Who you are and what you do now. Example: \"I am a product engineer building AI tools for creators.\"",
            "s2_occupation": "Role in one line. Example: \"Founder / builder\", \"Expert / practitioner\", \"Creator\".",
            "s2_audience": "Describe one concrete reader: role, level, pain. Example: \"28-year-old PM drowning in task chaos.\"",
            "s2_platforms": "Where you publish and which one is primary. Example: \"Telegram and LinkedIn; main channel is Telegram.\"",
            "s2_voice_tone": "Voice tone. Example: \"Direct, no fluff\" or \"Warm, conversational\".",
            "s2_formats": "Publishing formats. Example: \"Short posts and threads\".",
            "s2_niche_topics": "Topic breadth. Example: \"2-3 connected themes\".",
            "s2_goals": "Why you need content now. Select multiple options, then press Done.",
            "s2_signature_themes": "What to weave in often. Example: \"Personal stories + actionable how-to\".",
            "s2_personal_angle": "Your unique angle. Example: \"My own framework and career arc\".",
            "s2_human_design": "You can answer \"no\" or provide type/lens if this should influence content.",
            "s2_cadence": "Realistic publishing cadence. Example: \"Few times per week\".",
            "s2_reader_feel": "What feeling the reader should leave with. Example: \"Clarity, relief, and motivation to act.\"",
            "s2_avoid_topics": "Topics/formats you never publish. Example: \"Politics, rage-bait, manipulative clickbait.\"",
            "s2_anti_markers": (
                "Banned cliche phrases you do not want verbatim. "
                "Press Skip to keep default, or send a custom comma-separated list."
            ),
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
            "toggle_research": (
                "Enables pre-draft web research: the bot builds a short brief with current trends and sources from the live web. "
                "You can change this later in /profile or /settings."
            ),
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
    done_text = "✅ Готово" if lang == "ru" else "✅ Done"
    rows.append([InlineKeyboardButton(text=done_text, callback_data="onb:goal:done")])
    return _kb(rows, lang)


def _binary_kb(prefix: str, lang: str, *, include_back: bool = True) -> InlineKeyboardMarkup:
    yes = "✅ Да" if lang == "ru" else "✅ Yes"
    no = "❌ Нет" if lang == "ru" else "❌ No"
    return _kb(
        [
            [InlineKeyboardButton(text=yes, callback_data=f"{prefix}:yes")],
            [InlineKeyboardButton(text=no, callback_data=f"{prefix}:no")],
        ],
        lang,
        include_back=include_back,
    )


def _optional_text_kb(step: str, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if step in SKIPPABLE_STEPS:
        rows.append(_help_row(lang))
    return _kb(rows, lang, include_skip=step in SKIPPABLE_STEPS)


def _ready_kb(lang: str) -> InlineKeyboardMarkup:
    continue_label = "✅ Продолжить" if lang == "ru" else "✅ Continue"
    return _kb(
        [[InlineKeyboardButton(text=continue_label, callback_data="onb:ready:yes")]],
        lang,
        include_back=False,
    )


def _confirm_kb(kind: str, lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        ok, edit = "✅ Похоже", "✏️ Редактировать поля"
    else:
        ok, edit = "✅ Continue", "✏️ Edit fields"
    return _kb(
        [
            [InlineKeyboardButton(text=ok, callback_data=f"onb:{kind}:ok")],
            [InlineKeyboardButton(text=edit, callback_data=f"onb:{kind}:edit")],
        ],
        lang,
    )


def _confirm_edit_fork_kb(kind: str, lang: str) -> InlineKeyboardMarkup:
    if lang == "ru":
        edit_label = "✏️ Редактировать отвеченные поля"
        continue_label = "➡️ Продолжить с оставшимися вопросами"
    else:
        edit_label = "✏️ Edit answered fields"
        continue_label = "➡️ Continue with additional questions"
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
        style = fsm.get(
            "style_card_text",
            build_style_card(
                [],
                lang,
                avoid_topics=answers.get("s2_avoid_topics", ""),
                anti_markers=answers.get("s2_anti_markers", ""),
            ),
        )
        values = build_values_block(answers, lang)
        tribal = build_tribal_block(answers, lang)
        updates["values_block_text"] = values
        updates["tribal_block_text"] = tribal
        updates["system_prompt_text"] = build_system_prompt(answers, style, values, tribal, lang)
    await state.update_data(**updates)
    await _show_confirm_blocks(message, state, confirm_step, lang)


async def _send_prompt(target: Message, state: FSMContext, lang: str, step: str) -> None:
    await state.update_data(current_step=step)
    if step in {"s2_confirm", "s3_confirm", "s4_confirm", "s6_confirm"}:
        await _return_to_confirm(target, state, lang, step)
        return
    if step == "s2_goals":
        selected = set((await state.get_data()).get("goal_selected", []))
        text = _question_text("s2_goals", lang)
        goal_kb = _goal_kb(lang, selected)
        if step in SKIPPABLE_STEPS:
            goal_kb.inline_keyboard.insert(-1, _help_row(lang))
            goal_kb.inline_keyboard[-1] = _nav_row(lang, include_skip=True)
        await target.answer(text, reply_markup=goal_kb)
        return
    if step == "s1_ready":
        await target.answer(
            _question_text(step, lang),
            reply_markup=_ready_kb(lang),
        )
        return
    if step == "s3_samples":
        await target.answer(
            _question_text(step, lang),
            reply_markup=_sample_actions_kb(lang, include_skip=True),
        )
        return
    if step == "toggle_research":
        await target.answer(_question_text("toggle_warning", lang))
        toggle_kb = _binary_kb("onb:toggle:web", lang)
        toggle_kb.inline_keyboard.insert(-1, _help_row(lang))
        toggle_kb.inline_keyboard[-1] = _nav_row(lang, include_skip=True)
        await target.answer(_question_text(step, lang), reply_markup=toggle_kb)
        return
    if step == "toggle_review":
        toggle_kb = _binary_kb("onb:toggle:review", lang)
        toggle_kb.inline_keyboard.insert(-1, _help_row(lang))
        toggle_kb.inline_keyboard[-1] = _nav_row(lang, include_skip=True)
        await target.answer(_question_text(step, lang), reply_markup=toggle_kb)
        return
    if step == "s7_handoff":
        text = (
            "Теперь проверим в деле. Можешь сразу перейти в /new и дать короткую мысль для поста, или пропустить этот тест."
            if lang == "ru"
            else "Now we test in action. You can jump to /new with a short idea for a post, or skip this test."
        )
        await target.answer(text, reply_markup=_s7_handoff_kb(lang))
        return
    await target.answer(_question_text(step, lang), reply_markup=_optional_text_kb(step, lang))


def _next_step(step: str) -> str | None:
    idx = ONBOARDING_FLOW.index(step)
    if idx + 1 >= len(ONBOARDING_FLOW):
        return None
    return ONBOARDING_FLOW[idx + 1]


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


async def _persist_alias_if_needed(uid: int, source_key: str, value: str) -> None:
    alias = _alias_mappings().get(source_key)
    if not alias:
        return
    await _persist_answer(uid, alias, value, None)


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
            "Готово. Сохранить, перейти к тесту (опционально) и финальным настройкам?"
            if lang == "ru"
            else "Done. Save, move to optional test handoff, then final settings?"
        )
    await message.answer(text)
    await message.answer(help_text, reply_markup=_confirm_kb(step, lang))


async def _finish_onboarding(message: Message, state: FSMContext, uid: int, lang: str) -> None:
    fsm = await state.get_data()
    answers = dict(fsm.get("answers", {}))
    if "primary_language" not in answers:
        lang_value, _ = _primary_language_value(lang)
        answers["primary_language"] = lang_value
        await state.update_data(answers=answers)
    async with session_scope() as session:
        lang_value, lang_option = _primary_language_value(lang)
        await save_answer(
            session,
            uid,
            "primary_language",
            answers.get("primary_language", lang_value),
            option_index=lang_option,
            is_custom=False,
        )
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
        "Готово. У тебя есть 3 артефакта:\n\n"
        "1. STYLE CARD — сохрани отдельно.\n"
        "2. SYSTEM PROMPT — вставь в Claude Project / ChatGPT Custom Instructions / Gemini Gem.\n"
        "3. ПЕРВЫЙ ПОСТ — можешь публиковать как есть или допилить руками.\n\n"
        "Дальше подключи каналы и переходи в /new."
        if lang == "ru"
        else "Done. You have 3 artifacts:\n\n"
        "1. STYLE CARD - save it separately.\n"
        "2. SYSTEM PROMPT - paste into Claude Project / ChatGPT Custom Instructions / Gemini Gem.\n"
        "3. FIRST POST - publish as is or polish manually.\n\n"
        "Next: connect channels and continue in /new."
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
    await start_onboarding(
        message,
        state,
        uid=message.from_user.id,
        language_code=message.from_user.language_code,
        lang=_lang(data),
    )


async def start_onboarding(
    target: Message,
    state: FSMContext,
    *,
    uid: int,
    language_code: str | None,
    lang: str,
) -> None:
    async with session_scope() as session:
        await ensure_creator(
            session,
            telegram_user_id=uid,
            language_code=language_code,
        )
    await state.set_state(OnboardingStates.in_progress)
    fsm = await state.get_data()
    fsm_step = fsm.get("current_step")
    fsm_checkpoint = _checkpoint_step(fsm)
    async with session_scope() as session:
        answers = await get_profile_answers_map(session, uid)
    if "primary_language" not in answers:
        lang_value, _ = _primary_language_value(lang)
        answers["primary_language"] = lang_value
    samples_from_db: list[str] = []
    style_card_from_db = ""
    db_step = None
    if answers:
        raw_samples = answers.get(SAMPLES_DB_KEY)
        if raw_samples:
            try:
                parsed = json.loads(raw_samples)
                if isinstance(parsed, list):
                    samples_from_db = [str(item) for item in parsed if isinstance(item, str) and item.strip()]
            except Exception:
                samples_from_db = []
        style_card_from_db = (answers.get(STYLE_CARD_DB_KEY) or "").strip()
        if style_card_from_db:
            db_step = "s3_confirm"
        elif samples_from_db:
            db_step = "s3_samples"
        else:
            db_step = _resume_step_from_answers(answers)

    resolved_step: str | None = None
    if fsm_checkpoint and db_step:
        resolved_step = (
            fsm_checkpoint
            if FLOW_INDEX.get(fsm_checkpoint, -1) >= FLOW_INDEX.get(db_step, -1)
            else db_step
        )
    elif fsm_checkpoint:
        resolved_step = fsm_checkpoint
    elif db_step:
        resolved_step = db_step
    elif fsm_step:
        resolved_step = fsm_step

    if resolved_step:
        update_payload: dict[str, object] = {
            "current_step": resolved_step,
            "pending_edit_key": None,
            "pending_edit_confirm_step": None,
        }
        if answers:
            update_payload["answers"] = answers
            update_payload["goal_selected"] = _goal_selection_from_answer(answers.get("s2_goals"))
            update_payload["samples"] = fsm.get("samples", []) or samples_from_db
            if style_card_from_db:
                update_payload["style_card_text"] = style_card_from_db
        await state.update_data(**update_payload)
        await _send_prompt(target, state, lang, resolved_step)
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
    await _send_prompt(target, state, lang, "s1_ready")


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
            current_step = fsm.get("current_step")
            checkpoint = _checkpoint_step(fsm) or current_step or "s1_ready"
            await state.update_data(current_step=checkpoint)
            paused_text = (
                "Онбординг поставлен на паузу. Возобновим с последней контрольной точки через /onboarding. "
                "Если хочешь удалить прогресс, используй /cancel."
                if lang == "ru"
                else "Onboarding paused. Resume from your latest checkpoint with /onboarding. "
                "If you want to discard progress, use /cancel."
            )
            await callback.message.answer(paused_text)
            await callback.answer()
            return
        if action == "help":
            text = _help_text(fsm.get("current_step", "fallback"), lang)
            await callback.message.answer(text)
            await callback.answer()
            return
        if action == "skip":
            step = fsm.get("current_step")
            if not step or step not in SKIPPABLE_STEPS:
                await callback.answer(
                    "Этот вопрос обязателен." if lang == "ru" else "This question is required.",
                    show_alert=True,
                )
                return
            if step == "s3_samples":
                style_card = build_style_card(
                    [],
                    lang,
                    avoid_topics=fsm.get("answers", {}).get("s2_avoid_topics", ""),
                    anti_markers=fsm.get("answers", {}).get("s2_anti_markers", ""),
                )
                await _persist_answer(uid, STYLE_CARD_DB_KEY, style_card, None)
                await state.update_data(
                    style_card_text=style_card,
                    current_step="s3_confirm",
                    flow_stack=list(fsm.get("flow_stack", [])) + ["s3_samples"],
                )
                await _show_confirm_blocks(callback.message, state, "s3_confirm", lang)
                await callback.answer()
                return
            if step == "toggle_research":
                await _persist_answer(uid, "web_research", "Yes", 0)
                await state.update_data(
                    current_step="toggle_review",
                    flow_stack=list(fsm.get("flow_stack", [])) + ["toggle_research"],
                )
                await _send_prompt(callback.message, state, lang, "toggle_review")
                await callback.answer()
                return
            if step == "toggle_review":
                await _persist_answer(uid, "review_agent", "Yes", 0)
                await state.update_data(current_step="done")
                await _finish_onboarding(callback.message, state, uid, lang)
                await callback.answer()
                return

            answers = dict(fsm.get("answers", {}))
            if step == "s2_goals":
                answers["s2_goals"] = ""
                await state.update_data(answers=answers, goal_selected=[])
                await _persist_answer(uid, "s2_goals", "", None)
                await _persist_alias_if_needed(uid, "s2_goals", "")
            elif step == "s2_anti_markers":
                default_anti_markers = _default_anti_markers(lang)
                answers["s2_anti_markers"] = default_anti_markers
                await state.update_data(answers=answers)
                await _persist_answer(uid, "s2_anti_markers", default_anti_markers, None)
            else:
                key = _save_text_key(step)
                if key:
                    answers[key] = ""
                    await state.update_data(answers=answers)
                    await _persist_answer(uid, key, "", None)
                    await _persist_alias_if_needed(uid, key, "")
            next_step = _next_step(step)
            if next_step is None:
                await callback.answer()
                return
            if next_step == "s4_beliefs":
                await callback.message.answer(_question_text("s4_intro", lang))
            if next_step == "s5_reader_phrase":
                await callback.message.answer(_question_text("s5_intro", lang))
            await state.update_data(current_step=next_step, flow_stack=list(fsm.get("flow_stack", [])) + [step])
            if next_step == "s4_confirm":
                values_block = build_values_block(answers, lang)
                await state.update_data(values_block_text=values_block)
                await _show_confirm_blocks(callback.message, state, "s4_confirm", lang)
            elif next_step == "s6_confirm":
                style = fsm.get(
                    "style_card_text",
                    build_style_card(
                        [],
                        lang,
                        avoid_topics=answers.get("s2_avoid_topics", ""),
                        anti_markers=answers.get("s2_anti_markers", ""),
                    ),
                )
                values = fsm.get("values_block_text", build_values_block(answers, lang))
                tribal = build_tribal_block(answers, lang)
                system_prompt = build_system_prompt(answers, style, values, tribal, lang)
                await state.update_data(
                    tribal_block_text=tribal,
                    system_prompt_text=system_prompt,
                )
                await _show_confirm_blocks(callback.message, state, "s6_confirm", lang)
            else:
                await _send_prompt(callback.message, state, lang, next_step)
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
            await _persist_alias_if_needed(uid, "s2_goals", goal_text)
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
            await callback.message.answer(_reaction_text(lang))
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
            style_card = build_style_card(
                [],
                lang,
                avoid_topics=fsm.get("answers", {}).get("s2_avoid_topics", ""),
                anti_markers=fsm.get("answers", {}).get("s2_anti_markers", ""),
            )
            await _persist_answer(uid, STYLE_CARD_DB_KEY, style_card, None)
            await state.update_data(style_card_text=style_card, current_step="s3_confirm", flow_stack=list(fsm.get("flow_stack", [])) + ["s3_samples"])
            await _show_confirm_blocks(callback.message, state, "s3_confirm", lang)
            await callback.answer()
            return
        if parts[2] == "analyze":
            samples = list(fsm.get("samples", []))
            style_card = build_style_card(
                samples,
                lang,
                avoid_topics=fsm.get("answers", {}).get("s2_avoid_topics", ""),
                anti_markers=fsm.get("answers", {}).get("s2_anti_markers", ""),
            )
            await _persist_answer(uid, STYLE_CARD_DB_KEY, style_card, None)
            await state.update_data(style_card_text=style_card, current_step="s3_confirm", flow_stack=list(fsm.get("flow_stack", [])) + ["s3_samples"])
            await _show_confirm_blocks(callback.message, state, "s3_confirm", lang)
            await callback.answer()
            return

    if parts[1] == "s7":
        if parts[2] == "new":
            msg = (
                "Отлично. Открой /new и отправь короткую мысль — сделаем 3 разных угла."
                if lang == "ru"
                else "Great. Open /new and send a short thought - we will generate 3 different angles."
            )
            await callback.message.answer(msg)
            await state.update_data(current_step="toggle_research", flow_stack=list(fsm.get("flow_stack", [])) + ["s7_handoff"])
            await _send_prompt(callback.message, state, lang, "toggle_research")
            await callback.answer()
            return
        if parts[2] == "skip":
            await state.update_data(current_step="toggle_research", flow_stack=list(fsm.get("flow_stack", [])) + ["s7_handoff"])
            await _send_prompt(callback.message, state, lang, "toggle_research")
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
        await _persist_answer(uid, SAMPLES_DB_KEY, json.dumps(samples, ensure_ascii=False), None)
        ack = f"Образец сохранен ({len(samples)})." if lang == "ru" else f"Sample saved ({len(samples)})."
        await message.answer(ack, reply_markup=_sample_actions_kb(lang, include_skip=False))
        return

    if step == "s2_goals" and "e" in set(fsm.get("goal_selected", [])):
        answers = dict(fsm.get("answers", {}))
        merged = f"{answers.get('s2_goals', '')}; other: {text}".strip("; ")
        answers["s2_goals"] = merged
        await state.update_data(answers=answers)
        await _persist_answer(uid, "s2_goals", merged, None)
        await _persist_alias_if_needed(uid, "s2_goals", merged)
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
        await _persist_alias_if_needed(uid, key, text)
        pending_edit = fsm.get("pending_edit_key")
        if pending_edit:
            confirm_step = fsm.get("pending_edit_confirm_step", "s2_confirm")
            await _return_to_confirm(message, state, lang, confirm_step)
            return
        await message.answer(_reaction_text(lang))
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
            style = fsm.get(
                "style_card_text",
                build_style_card(
                    [],
                    lang,
                    avoid_topics=answers.get("s2_avoid_topics", ""),
                    anti_markers=answers.get("s2_anti_markers", ""),
                ),
            )
            values = fsm.get("values_block_text", build_values_block(answers, lang))
            tribal = build_tribal_block(answers, lang)
            system_prompt = build_system_prompt(answers, style, values, tribal, lang)
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
