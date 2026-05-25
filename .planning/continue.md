# Continue — production hardening

## Last action

Shipped Phase 2 vertical slice: `awaiting_input` → `session_inputs` → research (optional) → `DraftOrchestrator` → 3-option keyboard → follow-up menu → confirm → cover stub → publish (3 providers). Added `/sessions` resume, `/cancel`, worker `draft_round` job, multimodal stubs. **19** unit tests green.

## Next action

1. **Real OAuth token exchange** — Meta Graph + LinkedIn token endpoints; Fernet encrypt with `CREDENTIALS_ENCRYPTION_KEY`.
2. **Real publish adapters** — Telegram `sendMessage` to channel, IG Graph container, LinkedIn UGC post.
3. **STT + vision** — Whisper + vision model on `session_inputs` before `process_session_input`.
4. **Worker UX** — bot polls or Redis pubsub when `USE_WORKER=true` so user gets keyboard after job completes.

## Verification

```bash
pytest -m "not integration" -q
```

Manual: `/onboarding` → `/new` → text → pick draft → confirm → publish.

## Do not

- Do not cut IG/LI from v1 without ADR-0009 update.
- Do not commit `.env`.
