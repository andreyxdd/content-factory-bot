# STATE — content-factory-bot

Updated: handoff after Phase 1 + partial Phase 2 implementation.

## Milestone

v1 Telegram Content Factory bot (allowlisted creators, onboarding grill, content sessions, publish to TG + IG + LI).

## Phase status

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Scaffold | ✅ | Planning, ADRs, aiogram skeleton |
| 0.5 Worker | 🟡 | `JobQueue` + `cfbot-worker`; bot does not enqueue LLM jobs yet |
| 1 Onboarding | ✅ | 14-question grill FSM, `/profile` edit, `/settings`, locale detect |
| 2 Content session | 🟡 | `/new` setup FSM (research/cover toggles) → `awaiting_input`; no input/draft flow yet |
| 3 Multimodal | ⬜ | |
| 4 Publish | ⬜ | OAuth stubs only; token exchange not implemented |
| 5 Scheduled | ⬜ | |

## Verification last run

- `pytest -m "not integration"` → **14 passed**
- `test_job_queue` integration needs Redis (`pytest -m integration`)

## Key paths

- Spec: `.planning/SPEC.md`
- Flow: `.planning/FLOW-NEW-SESSION.md`
- Grill log: `.planning/grill/SESSION-2026-05-25.md`
- Gaps: `.planning/GAPS.md`
- Models: `src/content_factory_bot/db/models.py`
- Handoff: `.planning/continue.md`
