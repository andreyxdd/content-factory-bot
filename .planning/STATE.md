# STATE — content-factory-bot

Updated: Phase 2–4 core implemented (TDD, 19 unit tests).

## Milestone

v1 Telegram Content Factory bot (allowlisted creators, onboarding grill, content sessions, publish to TG + IG + LI).

## Phase status

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Scaffold | ✅ | Planning, ADRs, aiogram skeleton |
| 0.5 Worker | 🟡 | `JobQueue` + `cfbot-worker` runs `draft_round`; set `USE_WORKER=true` to enqueue from bot |
| 1 Onboarding | ✅ | 14-question grill FSM, `/profile` edit, `/settings`, locale detect |
| 2 Content session | ✅ | Input → research (optional) → drafts → follow-up → confirm → publish |
| 3 Multimodal | 🟡 | Photo/voice saved; STT/vision stubs (transcript placeholders) |
| 4 Publish | 🟡 | Publish orchestrator + artifact rows; OAuth stores stub tokens; real Graph/API TBD |
| 5 Scheduled | ⬜ | `/research` daily push not implemented |

## Verification last run

- `pytest -m "not integration"` → **19 passed**
- `test_job_queue` integration needs Redis (`pytest -m integration`)

## Key paths

- Spec: `.planning/SPEC.md`
- Flow: `.planning/FLOW-NEW-SESSION.md`
- Draft orchestrator: `src/content_factory_bot/services/draft.py`
- Session pipeline: `src/content_factory_bot/services/session_pipeline.py`
- Handoff: `.planning/continue.md`
