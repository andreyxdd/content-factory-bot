from __future__ import annotations

from dataclasses import dataclass
import re


S2_KEYS = (
    "s2_about",
    "s2_audience",
    "s2_platforms",
    "s2_goals",
    "s2_reader_feel",
    "s2_avoid_topics",
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
REQUIRED_KEYS = (
    "s2_about",
    "s2_audience",
    "s2_reader_feel",
    "s2_avoid_topics",
    "s5_voice_betrayal",
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
        "s2_about",
        "s2_audience",
        "s2_platforms",
        "s2_goals",
        "s2_reader_feel",
        "s2_avoid_topics",
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


def build_style_card(samples: list[str], lang: str) -> str:
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
                "  • Никогда не пиши: уточните после примеров\n"
                "  • Темы избегаю: см. шаг 2.6"
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
            "  • Never write: refine after samples\n"
            "  • Avoid topics: see step 2.6"
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
        ("важно отметить", "в заключение", "следует учитывать", "будущее за теми")
        if lang == "ru"
        else ("important to note", "in conclusion", "it is important to consider", "the future belongs to those")
    )
    for phrase in anti_candidates:
        if phrase not in joined:
            anti.append(phrase)
    anti_text = ", ".join(anti[:4]) if anti else ("общие ИИ-штампы" if lang == "ru" else "generic AI fillers")

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
            f"  • Соло-абзац как акцент: иногда\n\n"
            f"ЛЕКСИКА\n"
            f"  • Регистр: гибрид\n"
            f"  • Мат: точечно или нет\n"
            f"  • Англоязычные термины: по контексту ниши\n"
            f"  • Личные триггеры: выделить после правок\n"
            f"  • Пунктуация: тире/скобки по месту\n\n"
            f"АНТИ-МАРКЕРЫ\n"
            f"  • Никогда не пиши: {anti_text}\n"
            f"  • Темы избегаю: из шага 2.6"
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
        f"  • Solo sentence emphasis: sometimes\n\n"
        f"LEXICON\n"
        f"  • Register: hybrid\n"
        f"  • Profanity: sparse or none\n"
        f"  • EN terms: niche-dependent\n"
        f"  • Personal triggers: refine after edits\n"
        f"  • Punctuation traits: dash/parentheses when useful\n\n"
        f"ANTI-MARKERS\n"
        f"  • Never write: {anti_text}\n"
        f"  • Avoid topics: from step 2.6"
    )


def build_s2_summary(answers: dict[str, str], lang: str) -> str:
    if lang == "ru":
        return (
            "ПРОФИЛЬ-КАРТОЧКА\n"
            f"• Кто вы: {answers.get('s2_about', '—')}\n"
            f"• Аудитория: {answers.get('s2_audience', '—')}\n"
            f"• Платформы: {answers.get('s2_platforms', '—')}\n"
            f"• Цели: {answers.get('s2_goals', '—')}\n"
            f"• Что должен почувствовать читатель: {answers.get('s2_reader_feel', '—')}\n"
            f"• Что не публикуете: {answers.get('s2_avoid_topics', '—')}"
        )
    return (
        "PROFILE CARD\n"
        f"• Who you are: {answers.get('s2_about', '—')}\n"
        f"• Audience: {answers.get('s2_audience', '—')}\n"
        f"• Platforms: {answers.get('s2_platforms', '—')}\n"
        f"• Goals: {answers.get('s2_goals', '—')}\n"
        f"• Reader should feel: {answers.get('s2_reader_feel', '—')}\n"
        f"• Topics to avoid: {answers.get('s2_avoid_topics', '—')}"
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
    if lang == "ru":
        return (
            "Ты — мой ИИ-помощник по контенту. Ты пишешь от моего имени,\n"
            "для моей аудитории, в моём голосе. Не как робот — как я.\n\n"
            "# КТО Я\n"
            f"{answers.get('s2_about', '—')}\n\n"
            "# МОЯ АУДИТОРИЯ\n"
            f"{answers.get('s2_audience', '—')}\n\n"
            "# ПЛАТФОРМЫ\n"
            f"{answers.get('s2_platforms', '—')}\n\n"
            "# ЦЕЛЬ КОНТЕНТА\n"
            f"{answers.get('s2_goals', '—')}\n\n"
            "# МОЙ ГОЛОС\n"
            f"{style_card}\n\n"
            "# МОИ ЦЕННОСТИ И ПРОТИВОРЕЧИЯ\n"
            f"{values_block}\n\n"
            "# ЭМОЦИОНАЛЬНЫЙ ОТПЕЧАТОК\n"
            f"{answers.get('s2_reader_feel', '—')}\n\n"
            "# АНТИ-МАРКЕРЫ — ЧТО НИКОГДА НЕ ПИСАТЬ\n"
            f"{answers.get('s2_avoid_topics', '—')}\n\n"
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
        f"{answers.get('s2_goals', '—')}\n\n"
        "# MY VOICE\n"
        f"{style_card}\n\n"
        "# MY VALUES AND CONTRADICTIONS\n"
        f"{values_block}\n\n"
        "# EMOTIONAL IMPRINT\n"
        f"{answers.get('s2_reader_feel', '—')}\n\n"
        "# ANTI-MARKERS - NEVER WRITE\n"
        f"{answers.get('s2_avoid_topics', '—')}\n\n"
        "# FINAL CHECK BEFORE OUTPUT\n"
        f"{tribal_block}\n"
    )


def extract_first_url(text: str) -> str | None:
    match = re.search(r"https?://\\S+", text)
    if not match:
        return None
    return match.group(0).rstrip(").,!?")
