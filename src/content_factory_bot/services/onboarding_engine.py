from __future__ import annotations

import json
from dataclasses import dataclass
import re


S2_KEYS = (
    "s2_about",
    "s2_audience",
    "s2_platforms",
    "s2_goals",
    "s2_reader_feel",
    "s2_avoid_topics",
    "s2_anti_markers",
)

S4_KEYS = (
    "s4_beliefs",
    "s4_contradictions",
    "s4_boundaries",
    "s4_evolution",
)

S5_KEYS = (
    "s5_reader_phrase",
    "s5_voice_betrayal",
)

TOGGLE_KEYS = ("web_research", "review_agent")
YAML_REQUIRED_KEYS = (
    "primary_language",
    "occupation",
    "content_goals",
    "audience",
    "voice_tone",
    "formats",
    "niche_topics",
    "hard_limits",
    "signature_themes",
    "personal_angle",
    "human_design",
    "cadence",
)
REQUIRED_KEYS = (
    "s2_about",
    "s2_audience",
    "s2_goals",
    "s2_platforms",
    "s2_reader_feel",
    "s2_avoid_topics",
    "s2_anti_markers",
    "s4_beliefs",
    "s4_contradictions",
    "s4_boundaries",
    "s4_evolution",
    "s5_reader_phrase",
    "s5_voice_betrayal",
    "web_research",
    "review_agent",
    *YAML_REQUIRED_KEYS,
)


@dataclass(frozen=True)
class EditField:
    key: str
    label_en: str
    label_ru: str

    def label(self, lang: str) -> str:
        return self.label_ru if lang == "ru" else self.label_en


EDITABLE_FIELDS = (
    EditField("s2_about", "Who you are", "Кто вы"),
    EditField("s2_audience", "Audience", "Аудитория"),
    EditField("s2_platforms", "Platforms", "Платформы"),
    EditField("s2_goals", "Content goals", "Цели контента"),
    EditField("s2_reader_feel", "Reader feeling", "Эмоциональный эффект"),
    EditField("s2_avoid_topics", "Avoid topics", "Запретные темы"),
    EditField("s2_anti_markers", "Anti-markers", "Анти-маркеры"),
    EditField("s4_beliefs", "Contrarian beliefs", "Опорные убеждения"),
    EditField("s4_contradictions", "Inner contradictions", "Противоречия"),
    EditField("s4_boundaries", "Public boundaries", "Границы публичности"),
    EditField("s4_evolution", "View evolution", "Эволюция взглядов"),
    EditField("s5_reader_phrase", "Tribal phrase", "Фраза читателя"),
    EditField("s5_voice_betrayal", "Voice betrayal", "Предательство голоса"),
)


def editable_fields_for_confirm(confirm_step: str) -> tuple[EditField, ...]:
    if confirm_step in {"s2_confirm", "s3_confirm"}:
        allowed = set(S2_KEYS)
    elif confirm_step == "s4_confirm":
        allowed = set(S2_KEYS + S4_KEYS)
    elif confirm_step == "s6_confirm":
        allowed = set(S2_KEYS + S4_KEYS + S5_KEYS)
    else:
        allowed = {field.key for field in EDITABLE_FIELDS}
    return tuple(field for field in EDITABLE_FIELDS if field.key in allowed)


def required_answer_keys() -> set[str]:
    return set(REQUIRED_KEYS)


def ordered_profile_keys() -> tuple[str, ...]:
    return (
        "primary_language",
        "s2_about",
        "occupation",
        "s2_audience",
        "audience",
        "s2_platforms",
        "s2_goals",
        "content_goals",
        "voice_tone",
        "formats",
        "niche_topics",
        "s2_reader_feel",
        "s2_avoid_topics",
        "hard_limits",
        "s2_anti_markers",
        "signature_themes",
        "personal_angle",
        "human_design",
        "cadence",
        "s4_beliefs",
        "s4_contradictions",
        "s4_boundaries",
        "s4_evolution",
        "s5_reader_phrase",
        "s5_voice_betrayal",
        "web_research",
        "review_agent",
    )


def _guess_person(samples: list[str], lang: str) -> str:
    text = " ".join(samples).lower()
    first = text.count(" я ") + text.count(" i ")
    second = text.count(" ты ") + text.count(" you ")
    if first > second:
        return "1-е лицо (я)" if lang == "ru" else "1st person (I)"
    if second > first:
        return "2-е лицо (ты)" if lang == "ru" else "2nd person (you)"
    return "Смешанный" if lang == "ru" else "Mixed"


def build_style_card(
    samples: list[str],
    lang: str,
    *,
    avoid_topics: str = "",
    anti_markers: str = "",
) -> str:
    if not samples:
        if lang == "ru":
            return (
                "ГОЛОС\n"
                "  • Лицо: не задано (нет образцов)\n"
                "  • Самораскрытие: не задано\n"
                "  • Самоирония: не задано\n"
                "  • Противоречия: не задано\n\n"
                "ФОРМАТЫ\n"
                "  • Доминирующие: не определены\n"
                "  • Длина: не определена\n"
                "  • Финал: не определен\n\n"
                "РИТМ\n"
                "  • Динамичность: не определена\n"
                "  • Соло-абзац как акцент: не определен\n\n"
                "ЛЕКСИКА\n"
                "  • Регистр: не определен\n"
                "  • Мат: не определен\n"
                "  • Англоязычные термины: не определены\n"
                "  • Личные триггеры: не выделены\n"
                "  • Пунктуация: не определена\n\n"
                "АНТИ-МАРКЕРЫ\n"
                f"  • Никогда не пиши: {anti_markers or 'уточните после примеров'}\n"
                f"  • Темы избегаю: {avoid_topics or 'см. шаг 2.6'}"
            )
        return (
            "VOICE\n"
            "  • Person: not set (no samples)\n"
            "  • Self-disclosure: not set\n"
            "  • Self-irony: not set\n"
            "  • Contradictions: not set\n\n"
            "FORMATS\n"
            "  • Dominant: not detected\n"
            "  • Length: not detected\n"
            "  • Ending: not detected\n\n"
            "RHYTHM\n"
            "  • Burstiness: not detected\n"
            "  • Solo sentence emphasis: not detected\n\n"
            "LEXICON\n"
            "  • Register: not detected\n"
            "  • Profanity: not detected\n"
            "  • EN terms: not detected\n"
            "  • Personal triggers: not detected\n"
            "  • Punctuation traits: not detected\n\n"
            "ANTI-MARKERS\n"
            f"  • Never write: {anti_markers or 'refine after samples'}\n"
            f"  • Avoid topics: {avoid_topics or 'see step 2.6'}"
        )

    person = _guess_person(samples, lang)
    total = sum(len(x) for x in samples)
    avg = total // max(len(samples), 1)
    if lang == "ru":
        length = "короткая" if avg < 500 else "средняя" if avg < 1500 else "длинная"
    else:
        length = "short" if avg < 500 else "medium" if avg < 1500 else "long"
    anti = []
    joined = " ".join(samples).lower()
    anti_candidates = (
        ("в заключение", "важно отметить", "в современном быстро меняющемся мире", "раскройте свой потенциал")
        if lang == "ru"
        else ("in conclusion", "it is important to note", "in today's fast-paced world", "unlock your potential")
    )
    for phrase in anti_candidates:
        if phrase not in joined:
            anti.append(phrase)
    anti_text = anti_markers or (
        ", ".join(anti[:4]) if anti else ("общие ИИ-штампы" if lang == "ru" else "generic AI fillers")
    )

    if lang == "ru":
        return (
            f"ГОЛОС\n"
            f"  • Лицо: {person}\n"
            f"  • Самораскрытие: средний уровень\n"
            f"  • Самоирония: умеренная\n"
            f"  • Противоречия: присутствуют\n\n"
            f"ФОРМАТЫ\n"
            f"  • Доминирующие: история + вывод, рефлексия\n"
            f"  • Длина: {length}\n"
            f"  • Финал: открытый вопрос или вывод\n\n"
            f"РИТМ\n"
            f"  • Динамичность: средняя\n"
            f"  • Соло-абзац как акцент: иногда\n"
            f"  • Списки: текстовые без буллетов\n\n"
            f"ЛЕКСИКА\n"
            f"  • Регистр: гибрид\n"
            f"  • Мат: точечно или нет\n"
            f"  • Англоязычные термины: по контексту ниши\n"
            f"  • Личные триггеры: выделить после правок\n"
            f"  • Пунктуация: тире/скобки по месту\n\n"
            f"АНТИ-МАРКЕРЫ\n"
            f"  • Никогда не пиши: {anti_text}\n"
            f"  • Темы избегаю: {avoid_topics or 'из шага 2.6'}"
        )
    return (
        f"VOICE\n"
        f"  • Person: {person}\n"
        f"  • Self-disclosure: medium\n"
        f"  • Self-irony: mild\n"
        f"  • Contradictions: present\n\n"
        f"FORMATS\n"
        f"  • Dominant: story+insight, reflection\n"
        f"  • Length: {length}\n"
        f"  • Ending: open question or punchline\n\n"
        f"RHYTHM\n"
        f"  • Burstiness: medium\n"
        f"  • Solo sentence emphasis: sometimes\n"
        f"  • Lists: plain-text lists\n\n"
        f"LEXICON\n"
        f"  • Register: hybrid\n"
        f"  • Profanity: sparse or none\n"
        f"  • EN terms: niche-dependent\n"
        f"  • Personal triggers: refine after edits\n"
        f"  • Punctuation traits: dash/parentheses when useful\n\n"
        f"ANTI-MARKERS\n"
        f"  • Never write: {anti_text}\n"
        f"  • Avoid topics: {avoid_topics or 'from step 2.6'}"
    )


def build_s2_summary(answers: dict[str, str], lang: str) -> str:
    if lang == "ru":
        return (
            "ПРОФИЛЬ-КАРТОЧКА\n"
            f"• Кто вы: {answers.get('s2_about', '—')}\n"
            f"• Роль: {answers.get('occupation', '—')}\n"
            f"• Аудитория: {answers.get('s2_audience', '—')}\n"
            f"• Платформы: {answers.get('s2_platforms', '—')}\n"
            f"• Тон: {answers.get('voice_tone', '—')}\n"
            f"• Форматы: {answers.get('formats', '—')}\n"
            f"• Тематический охват: {answers.get('niche_topics', '—')}\n"
            f"• Цели: {answers.get('s2_goals', '—')}\n"
            f"• Сигнатурные темы: {answers.get('signature_themes', '—')}\n"
            f"• Личный угол: {answers.get('personal_angle', '—')}\n"
            f"• Human Design: {answers.get('human_design', '—')}\n"
            f"• Ритм: {answers.get('cadence', '—')}\n"
            f"• Что должен почувствовать читатель: {answers.get('s2_reader_feel', '—')}\n"
            f"• Что не публикуете: {answers.get('s2_avoid_topics', '—')}\n"
            f"• Анти-маркеры: {answers.get('s2_anti_markers', '—')}"
        )
    return (
        "PROFILE CARD\n"
        f"• Who you are: {answers.get('s2_about', '—')}\n"
        f"• Occupation: {answers.get('occupation', '—')}\n"
        f"• Audience: {answers.get('s2_audience', '—')}\n"
        f"• Platforms: {answers.get('s2_platforms', '—')}\n"
        f"• Tone: {answers.get('voice_tone', '—')}\n"
        f"• Formats: {answers.get('formats', '—')}\n"
        f"• Topic scope: {answers.get('niche_topics', '—')}\n"
        f"• Goals: {answers.get('s2_goals', '—')}\n"
        f"• Signature themes: {answers.get('signature_themes', '—')}\n"
        f"• Personal angle: {answers.get('personal_angle', '—')}\n"
        f"• Human Design: {answers.get('human_design', '—')}\n"
        f"• Cadence: {answers.get('cadence', '—')}\n"
        f"• Reader should feel: {answers.get('s2_reader_feel', '—')}\n"
        f"• Topics to avoid: {answers.get('s2_avoid_topics', '—')}\n"
        f"• Anti-markers: {answers.get('s2_anti_markers', '—')}"
    )


def build_values_block(answers: dict[str, str], lang: str) -> str:
    if lang == "ru":
        return (
            "ЦЕННОСТИ И ПРОТИВОРЕЧИЯ\n"
            f"• Немейнстримные убеждения: {answers.get('s4_beliefs', '—')}\n"
            f"• Внутренние противоречия: {answers.get('s4_contradictions', '—')}\n"
            f"• Границы публичности: {answers.get('s4_boundaries', '—')}\n"
            f"• Эволюция взглядов: {answers.get('s4_evolution', '—')}"
        )
    return (
        "VALUES AND CONTRADICTIONS\n"
        f"• Contrarian beliefs: {answers.get('s4_beliefs', '—')}\n"
        f"• Inner contradictions: {answers.get('s4_contradictions', '—')}\n"
        f"• Public boundaries: {answers.get('s4_boundaries', '—')}\n"
        f"• View evolution: {answers.get('s4_evolution', '—')}"
    )


def build_tribal_block(answers: dict[str, str], lang: str) -> str:
    if lang == "ru":
        return (
            "ПРОВЕРКА СВОЕГО ЧИТАТЕЛЯ\n"
            f"• Фраза идеального читателя: {answers.get('s5_reader_phrase', '—')}\n"
            f"• Предательство голоса: {answers.get('s5_voice_betrayal', '—')}"
        )
    return (
        "TRIBAL CHECK\n"
        f"• Ideal reader phrase: {answers.get('s5_reader_phrase', '—')}\n"
        f"• Voice betrayal: {answers.get('s5_voice_betrayal', '—')}"
    )


def build_system_prompt(
    answers: dict[str, str],
    style_card: str,
    values_block: str,
    tribal_block: str,
    lang: str,
) -> str:
    examples_raw = answers.get("s3_samples", "")
    examples: list[str] = []
    if examples_raw:
        try:
            parsed = json.loads(examples_raw)
            if isinstance(parsed, list):
                examples = [str(chunk).strip() for chunk in parsed if str(chunk).strip()][:3]
        except Exception:
            examples = [chunk.strip() for chunk in examples_raw.split("\n\n") if chunk.strip()][:3]
    examples_block = "\n".join(f"- {item}" for item in examples) if examples else "- n/a"
    banned_topics = answers.get("s4_boundaries", "—")
    anti_markers = answers.get("s2_anti_markers", "—")
    reader_phrase = answers.get("s5_reader_phrase", "—")
    content_goal = answers.get("s2_goals", "—")
    tribal_goal = answers.get("s5_reader_phrase", "—")

    if lang == "ru":
        return (
            "Ты — мой ИИ-помощник по контенту. Ты пишешь от моего имени,\n"
            "для моей аудитории, в моём голосе. Не как робот — как я.\n\n"
            "# КТО Я\n"
            f"{answers.get('s2_about', '—')}\n"
            f"Цели: {content_goal}\n\n"
            "# МОЯ АУДИТОРИЯ\n"
            f"{answers.get('s2_audience', '—')}\n\n"
            "# ПЛАТФОРМЫ\n"
            f"{answers.get('s2_platforms', '—')}\n\n"
            "# ЦЕЛЬ КОНТЕНТА\n"
            f"{content_goal}\n"
            f"Tribal phrase: {tribal_goal}\n\n"
            "# МОЙ ГОЛОС\n"
            f"{style_card}\n\n"
            "# МОИ ЦЕННОСТИ И ПРОТИВОРЕЧИЯ\n"
            f"{values_block}\n\n"
            "# ЭМОЦИОНАЛЬНЫЙ ОТПЕЧАТОК\n"
            f"{reader_phrase}\n\n"
            "# ФОРМАТЫ ПОСТОВ КОТОРЫЕ Я ИСПОЛЬЗУЮ\n"
            "1. История + вывод\n"
            "2. Конфликт / противоречие\n"
            "3. Практика / инструмент\n"
            "4. Рефлексия\n\n"
            "# ПРАВИЛА ПИСЬМА (на основе моего стиля)\n"
            "- Личное местоимение \"я\", не \"автор\".\n"
            "- Чередуй короткие и длинные предложения.\n"
            "- Соло-предложение как абзац - для акцента.\n"
            "- Финал - мысль или вопрос, не прямой CTA.\n"
            "- Самоирония без самобичевания.\n"
            "- Признавай противоречия там, где они есть.\n\n"
            "# АНТИ-МАРКЕРЫ — ЧТО НИКОГДА НЕ ПИСАТЬ\n"
            f"{anti_markers}\n"
            "Запрещённые конструкции:\n"
            "- важно отметить, следует учитывать, в заключение\n"
            "- это не X - это Y как драматическая концовка\n"
            "- будущее за теми кто... без личного угла\n"
            "- пустые слоганы и списки без истории\n"
            f"Запрещённые темы: {banned_topics}\n\n"
            "# QUALITY GATE — ВНУТРЕННИЙ ЧЕК ПЕРЕД ВЫДАЧЕЙ\n"
            "1. Generic detector: убирай AI-фразы и шаблонные контрасты.\n"
            "2. Rhythm: разрывай ритм, если 3+ фразы одной длины подряд.\n"
            "3. Specificity: добавляй личное я, число/дату/имя или конкретный факт.\n"
            "4. Anti-slop: удаляй пустые слоганы и псевдо-умные формулы.\n\n"
            "# TRIBAL CHECK — ФИНАЛЬНЫЙ ВОПРОС ПЕРЕД ВЫДАЧЕЙ\n"
            f"\"{reader_phrase}\" - попадает ли пост в это?\n\n"
            "# ПРИМЕРЫ МОИХ ПОСТОВ (для калибровки тона)\n"
            f"{examples_block}\n\n"
            "# ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД ВЫДАЧЕЙ\n"
            f"{tribal_block}\n"
        )
    return (
        "You are my AI content copilot. Write on my behalf,\n"
        "for my audience, in my voice. Not like a robot - like me.\n\n"
        "# WHO I AM\n"
        f"{answers.get('s2_about', '—')}\n\n"
        "# MY AUDIENCE\n"
        f"{answers.get('s2_audience', '—')}\n\n"
        "# PLATFORMS\n"
        f"{answers.get('s2_platforms', '—')}\n\n"
        "# CONTENT GOAL\n"
        f"{content_goal}\n"
        f"Tribal phrase: {tribal_goal}\n\n"
        "# MY VOICE\n"
        f"{style_card}\n\n"
        "# MY VALUES AND CONTRADICTIONS\n"
        f"{values_block}\n\n"
        "# EMOTIONAL IMPRINT\n"
        f"{reader_phrase}\n\n"
        "# POST FORMATS I USE\n"
        "1. Story + takeaway\n"
        "2. Conflict / contradiction\n"
        "3. Practical tool\n"
        "4. Reflection\n\n"
        "# WRITING RULES (from my style)\n"
        "- Use first person \"I\".\n"
        "- Alternate short and long sentences.\n"
        "- Use solo-sentence paragraph for emphasis.\n"
        "- End with thought or question, not hard CTA.\n"
        "- Keep self-irony without self-destruction.\n"
        "- Admit contradictions when real.\n\n"
        "# ANTI-MARKERS - NEVER WRITE\n"
        f"{anti_markers}\n"
        "Forbidden constructions:\n"
        "- it is important to note / in conclusion / should be considered\n"
        "- this is not X, this is Y dramatic closer\n"
        "- the future belongs to those who... without personal angle\n"
        "- empty slogans and listicles without story\n"
        f"Forbidden topics: {banned_topics}\n\n"
        "# QUALITY GATE - INTERNAL CHECK\n"
        "1. Generic detector: remove AI filler phrases.\n"
        "2. Rhythm: break 3+ same-length sentence streaks.\n"
        "3. Specificity: include first-person + concrete detail.\n"
        "4. Anti-slop: remove empty slogan patterns.\n\n"
        "# TRIBAL CHECK - FINAL QUESTION\n"
        f"\"{reader_phrase}\" - does this post hit it?\n\n"
        "# EXAMPLES OF MY POSTS (tone calibration)\n"
        f"{examples_block}\n\n"
        "# FINAL CHECK BEFORE OUTPUT\n"
        f"{tribal_block}\n"
    )


def extract_first_url(text: str) -> str | None:
    match = re.search(r"https?://\S+", text)
    if not match:
        return None
    return match.group(0).rstrip(").,!?")
