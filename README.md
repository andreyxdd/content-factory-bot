# Content Factory Bot (Telegram)

Telegram bot for allowlisted creators: interactive **onboarding** (personality profile), **content sessions** with multimodal input and 3+1 draft menus, publish to connected providers.

## Planning

- [PROJECT](.planning/PROJECT.md) — vision and stack
- [SPEC](.planning/SPEC.md) — functional spec
- [COMMANDS](.planning/COMMANDS.md) — command catalog
- [REVIEW](.planning/REVIEW.md) — risks and improvements
- [ROADMAP](.planning/ROADMAP.md) — phases
- [Grill session](.planning/grill/SESSION-2026-05-25.md) — open decisions

Domain language: [CONTEXT.md](CONTEXT.md). Decisions: [docs/adr/](docs/adr/).

## Quick start (local)

```bash
cp .env.example .env
# Required: BOT_TOKEN, ALLOWLIST_TELEGRAM_IDS (your Telegram numeric user id)
# Required: DATABASE_URL, REDIS_URL
# Recommended: OAUTH_STATE_SECRET, PUBLIC_BASE_URL (for /providers OAuth links)
# Optional: OPENROUTER_API_KEY (Phase 2+ LLM jobs)

docker compose up -d postgres redis
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cfbot-migrate   # or: AUTO_CREATE_TABLES=true in .env for boot-time create_all (dev only)

# Terminal 1 — bot
python -m content_factory_bot
# or: cfbot

# Terminal 2 — OAuth API (Instagram / LinkedIn connect buttons)
cfbot-api
# or: uvicorn content_factory_bot.api.app:app --host 0.0.0.0 --port 8000

# Terminal 3 — background worker (optional until LLM jobs wired)
cfbot-worker
```

Get your Telegram user id from `@userinfobot`. Add it to `ALLOWLIST_TELEGRAM_IDS` in `.env`.

Tests: `pytest -m "not integration"` (14 unit). With Redis: `pytest -m integration`.

OAuth redirect setup: [.planning/OAUTH-SETUP.md](.planning/OAUTH-SETUP.md).

## Status

Phase 0 scaffold — handlers and DB migrations in Phase 1+.
