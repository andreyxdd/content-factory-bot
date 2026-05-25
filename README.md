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

## Quick start

```bash
cp .env.example .env
# set BOT_TOKEN, DATABASE_URL, ALLOWLIST_TELEGRAM_IDS
docker compose up -d postgres
uv sync   # or: pip install -e ".[dev]"
uv run python -m content_factory_bot

# OAuth API (Instagram / LinkedIn connect)
uv run uvicorn content_factory_bot.api.app:app --host 0.0.0.0 --port 8000
```

OAuth redirect setup: [.planning/OAUTH-SETUP.md](.planning/OAUTH-SETUP.md).

## Status

Phase 0 scaffold — handlers and DB migrations in Phase 1+.
