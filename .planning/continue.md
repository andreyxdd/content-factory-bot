# Continue — Phase 2 content session (input → drafts)

## Last action

Implemented Phase 1 onboarding grill (14 questions, 3+1 keyboards, profile persistence) and partial Phase 2: `/new` setup FSM with research/cover toggles → `content_sessions` row in `awaiting_input`. Committed on `main` (6 commits ending `e04384a`). Evidence: `pytest -m "not integration"` — 14 passed.

## Next action

Add a message handler for `ContentSession.state == "awaiting_input"`: persist text to `session_inputs`, then enqueue a worker job `draft_round` (or call `DraftOrchestrator` inline first). **Success criterion:** allowlisted user with completed onboarding runs `/new` → start session → sends text → receives 3-option inline keyboard (stub LLM JSON is fine for first green test).

Start with **TDD**: `tests/test_draft_round.py` — given profile + session input, returns 3 strings.

## Why

Roadmap Phase 2 blocks everything else (confirm, `/sessions` resume, research step, review step). Input capture is the narrowest vertical slice after `/new` setup already merged.

## Open threads

- Worker queue exists but bot never calls `JobQueue.enqueue` yet — wire when draft step exceeds ~5s or from the start for consistency with ADR-0010.
- `/sessions` list/resume not implemented.
- `/cancel` does not clear FSM or close active session.
- OAuth callbacks are stubs (no token storage).
- Meta/LinkedIn app review still on critical path for v1 publish (see `.planning/INSTAGRAM-META.md`).

## Do not

- Do not cut IG/LI from v1 without updating ADR-0009 and grill log — user chose all three providers live.
- Do not add LangChain/agent harness for drafts — use `LLMClient` + in-process orchestrator per ADR-0006.
- Do not run `git push` unless asked — local `main` only.
- Do not commit `.env` (gitignored).

## Local run (reminder)

```bash
cp .env.example .env   # BOT_TOKEN, ALLOWLIST_TELEGRAM_IDS, DATABASE_URL, REDIS_URL
docker compose up -d postgres redis
source .venv/bin/activate && pip install -e ".[dev]"
python -m content_factory_bot
```

Optional: `cfbot-api` for `/providers` OAuth links (`PUBLIC_BASE_URL`, `OAUTH_STATE_SECRET`).
