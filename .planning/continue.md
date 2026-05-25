# Continue — v1 production hardening

## Last action

Autonomous v1 closed ROADMAP phases 0.5–4 on `main` (commits `3c4a364`…`21d2fd3`). Evidence: `pytest -m "not integration" -q` → **27 passed**, working tree clean at `21d2fd3`.

## Next action

Implement real OAuth token exchange in `src/content_factory_bot/api/oauth.py` for Instagram and LinkedIn (replace `stub:{code}` storage with Meta Graph + LinkedIn token endpoints). Add a unit test with mocked `httpx` responses. Re-run `pytest -m "not integration" -q` before claiming done.

## Why

Adapters in `services/publish/adapters.py` call live APIs only when `access_token` is real; callbacks still store stub tokens. ADR-0009 requires all three providers publishable in production — code paths exist but credentials are not production-grade yet.

## Open threads

- Meta / LinkedIn app review is operator calendar work (`.planning/INSTAGRAM-META.md`) — not blocked on bot code.
- Alembic migrations not started; schema still via `create_tables()` on boot.
- Phase 5 (`/research` scheduled push) explicitly skipped in ROADMAP.
- Cover step still stub (`services/cover.py`); image models in `.planning/MODEL-MATRIX.md` unwired.
- `USE_WORKER=true` requires `cfbot-worker` running; bot polls DB up to 120s (`worker/wait.py`).

## Do not

- Do not re-implement draft/session flow — Phase 2 is done (`handlers/content_session.py`, `services/session_pipeline.py`).
- Do not commit `.env` (gitignored).
- Do not treat stub publish URLs (`stub.local`, `instagram.com/p/stub-*`) as production success.
- Do not run `git push` unless the user asks.

## Local run (reminder)

```bash
cp .env.example .env   # BOT_TOKEN, ALLOWLIST_TELEGRAM_IDS, DATABASE_URL, REDIS_URL
docker compose up -d postgres redis
source .venv/bin/activate && pip install -e ".[dev]"
python -m content_factory_bot   # optional: cfbot-worker, cfbot-api for OAuth
```

Manual smoke: `/onboarding` → `/new` → text → pick draft → confirm → publish. Link TG: `/providers` → forward channel post.
