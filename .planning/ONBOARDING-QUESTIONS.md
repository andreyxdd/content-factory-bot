# Onboarding grill — question bank

**Mode:** grill-me style — **one question at a time**. Message body lists numbered options (⭐ on recommended); inline keyboard shows **one button per option** (`1`…`N`). **Custom reply** (free text) only on **3-option** questions — not on 2-option choice-only items.

**14 questions**, ~6–10 minutes. Answers stored per `question_key`; **writing step** and **review step** load full set as context.

**Edit later:** `/profile` → list answers → tap question → re-run that question only (same 3+1 UI).

Load at runtime from `src/content_factory_bot/onboarding/questions.yaml`.

---

## Question order

| # | `question_key` | Purpose |
|---|----------------|---------|
| 1 | `primary_language` | Bot UI + draft language (`en` / `ru`) (**2-option, choice-only**) |
| 2 | `occupation` | Who they are professionally |
| 3 | `content_goals` | Why they post |
| 4 | `audience` | Who reads |
| 5 | `voice_tone` | How they sound |
| 6 | `formats` | Thread / post / carousel / long-form |
| 7 | `niche_topics` | What they usually cover |
| 8 | `hard_limits` | Taboos, never mention |
| 9 | `signature_themes` | Themes to weave in often |
| 10 | `personal_angle` | Stories, framework, beliefs — unmistakably *theirs* |
| 11 | `human_design` | HD type if they use it; or skip |
| 12 | `cadence` | Posting rhythm |
| 13 | `web_research` | Default **web research** at `/new` → `research_default_enabled` (**2-option, choice-only**) |
| 14 | `review_agent` | Default **review step** → `review_enabled` (**2-option, choice-only**) |

---

## Example item (YAML shape)

```yaml
- key: content_goals
  prompts:
    en: "What is your main content goal right now?"
    ru: "Какая главная цель вашего контента сейчас?"
  recommended: 0
  options:
    en:
      - "Build authority in my niche"
      - "Grow audience / reach"
      - "Generate leads or clients"
    ru:
      - "Укрепить экспертизу в нише"
      - "Рост аудитории и охватов"
      - "Лиды и клиенты"
```

Bot shows numbered `options[lang]` in the message; ⭐ on `recommended` index; buttons are `1`, `2`, `3`.

---

## Grill-me rules (onboarding FSM)

0. Before Q1: bot UI already in **Telegram client locale** (see `.planning/I18N.md`). Q1 `primary_language` pre-selects ⭐ on detected language.
1. Ask all 14 sequentially; no skipping ahead.
2. Show **recommendation** via ⭐ on the numbered option row (no separate “Suggested:” line).
3. **3-option questions:** free text in `in_progress` allowed; typed `1`/`2`/`3` map to options. **2-option (choice-only):** buttons `1`/`2` only; no free text; footer `onboarding_pick_only`. Ignore `/…`, whitespace-only, and non-text everywhere.
4. On completion: `personality_profile.ready = true`, snapshot `profile_version`.
5. `/onboarding` full re-run asks confirm; active session blocked (gap G-ONB1).

---

## Custom reply handling

Store verbatim text; mark `answer_source: custom`. Writing step treats custom answers as highest-signal context.
