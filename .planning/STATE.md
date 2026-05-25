# STATE — content-factory-bot

Updated: handoff after autonomous v1 (phases 0.5–4 code-complete).

## Milestone

v1 Telegram Content Factory bot — **code-complete** for ROADMAP phases 0–4. Production IG/LI still needs Meta/LinkedIn app review and real tokens.

## Phase status

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Scaffold | ✅ | |
| 0.5 Worker | ✅ | `USE_WORKER=true` → enqueue + DB poll + draft keyboard |
| 1 Onboarding | ✅ | `/cancel` closes FSM + session |
| 2 Content session | ✅ | Full draft → confirm → publish flow |
| 3 Multimodal | ✅ | Telegram file download + STT + vision |
| 4 Publish | ✅ | Per-provider adapters + TG channel link + retry |
| 5 Scheduled | ⬜ | Out of scope |

## Verification last run

```
pytest -m "not integration" -q
37 passed, 2 deselected
pytest tests/test_schema.py -m integration -q
1 passed (requires Postgres on :5433 or TEST_DATABASE_URL)
```

## Key paths

- Publish: `src/content_factory_bot/services/publish/`
- Multimodal: `services/stt.py`, `services/vision.py`, `services/telegram_files.py`
- Worker wait: `src/content_factory_bot/worker/wait.py`
