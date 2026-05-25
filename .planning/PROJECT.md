# Content Factory Bot — PROJECT

## Vision

Telegram bot for a **closed cohort** of creators. Each Creator gets a persisted **personality profile** (onboarding grill), then runs **content sessions** that accept multimodal input, produce three draft options per round (plus custom reply), and publish to connected **providers** (Telegram channel/group, Instagram, LinkedIn).

Adapted from [OpenClaw Content Factory](https://github.com/hesamsheikh/awesome-openclaw-usecases/blob/main/usecases/content-factory.md): same *research → write → visual* spirit, but **interactive** and **Telegram-native** (inline keyboards, commands, FSM)—not Discord channels or scheduled subagents.

## Non-goals (MVP)

- Public bot discovery / open signup
- Discord or multi-channel agent orchestration inside chat
- Fully unattended daily 8 AM pipeline (candidate for v2)
- YouTube script / thumbnail pipeline unless scoped later

## Success criteria

1. Allowlisted Creator completes onboarding; profile persisted.
2. `/new` → multimodal capture → ≥1 draft round → confirm → publish to ≥1 provider → urls returned; session closed.
3. Creator lists sessions by title and resumes an in-progress session.
4. Provider connections stored securely; publish respects one-time subset selection.

## Stack (proposed — ADR-0001)

- **Runtime:** Python 3.12+
- **Bot:** aiogram 3.x (FSM, inline keyboards)
- **API:** FastAPI (webhooks, OAuth callbacks, health)
- **DB:** PostgreSQL (profiles, sessions, drafts, connections, publish log)
- **Queue (v2):** Redis + worker for long LLM / media jobs
- **AI:** in-process `DraftOrchestrator` → OpenRouter (OpenAI-compatible API), structured JSON drafts; STT/vision separate; see `.planning/AI-STACK.md`

## Repository layout

```
.planning/          # plans, grill logs, roadmap
docs/adr/           # hard-to-reverse decisions
src/content_factory_bot/
CONTEXT.md          # domain glossary only
```

## Open decisions (grill in progress)

See `.planning/grill/SESSION-2026-05-25.md`. Blocking Q1: allowlist governance model.
