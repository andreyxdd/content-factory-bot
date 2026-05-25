# Planning gaps — tracker

## Closed

| Gap | Resolution |
|-----|------------|
| v1 publish | All three providers live (ADR-0009) |
| Research topic | After input (A) |
| Two-menu UX | Original brief in SPEC |
| Cover toggle | `/new` setup before input |
| TG channel connect | Forward message + admin check |
| Post format | One draft + provider adapters at publish |
| Token encryption | Fernet + `CREDENTIALS_ENCRYPTION_KEY` |
| Media storage | S3-compatible (R2 ok) |
| Worker | Redis worker from v1 (ADR-0010) |
| Onboarding | Grill-me 3+1, `questions.yaml`, `/profile` edit |
| Review step | Optional at onboarding; GPT-4o primary (ADR-0011) |
| Alembic migrations | `cfbot-migrate`, baseline `20260525_0001`; ADR-0012 |

## Still open

- [ ] **Meta / LinkedIn app review** calendar (see `.planning/INSTAGRAM-META.md`) — operator task
- [ ] **v1 target date** / contingency if review slips
- [ ] Full FSM enum in SPEC (draft list)
- [ ] Per-provider adapter rules document
- [ ] OpenRouter image route proof for Flux/DALL·E
- [ ] S3 media upload (storage_ref is Telegram `file_id` for now)

## Implemented (autonomous v1)

| Item | Location |
|------|----------|
| STT | `services/stt.py` — Whisper API or stub |
| Vision | `services/vision.py` — LLM image or stub |
| Fernet credentials | `services/credentials.py` |
| Publish adapters | `services/publish/adapters.py` |
| Worker notify | `worker/wait.py` + handler poll |
