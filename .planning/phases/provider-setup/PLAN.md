# Provider setup phase — execution plan

Source: grill session 2026-05-26 (Q1–Q9) in `.planning/grill/SESSION-2026-05-25.md`, `CONTEXT.md`, `.planning/DECISIONS.md`.

## Goal

Creators finish personality `/onboarding`, then link publish targets via **`/providers`** (no `/connect`). `/new` requires **setup complete** (≥1 active connection). Sessions publish only to **session destinations** chosen from connected providers.

## Verification table

| Step | Kind | Success criterion | Verification |
|------|------|-------------------|--------------|
| 1 | backend | `is_setup_complete` true iff ≥1 active connection | `pytest tests/test_providers_service.py -q` |
| 2 | backend | Publish uses session `destinations_json` only | `pytest tests/test_publish.py -q` |
| 3 | ui | Post-onboarding sends providers screen + skip | `pytest tests/test_providers_screen.py -q` |
| 4 | ui | `/new` blocked when setup incomplete | service + handler tests |
| 5 | ui | `/new` setup toggles when 2+ connected | `test_providers_service` / session tests |
| 6 | ui | TG forward rejected if bot not admin | `test_providers_telegram_link.py` |
| 7 | backend | OAuth callback notifies Creator via DM | `test_telegram_notify.py` |
| 8 | ui | Disconnect button + `/disconnect` | `test_providers_service.py` |
| 9 | all | Full unit suite green | `pytest -m "not integration" -q` |

## Behavior summary (locked)

- `/onboarding` complete → auto **providers screen** (same as `/providers`).
- **Skip for now** on that screen; `/profile` `/settings` `/providers` still work; `/new` blocked with reminder.
- **≥1** active connection unlocks `/new`.
- **Session destinations:** 1 connected → implicit; 2+ → toggles default all ON.
- **Disconnect:** inline confirm + `/disconnect <provider>`.
- **Telegram link:** `getChatMember` admin check before save.
- **OAuth:** Telegram DM + HTML page on success/failure.

## Out of scope

- Real Meta/LinkedIn token exchange (stub remains).
- Meta/LinkedIn app review (operator).
