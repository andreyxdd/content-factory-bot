# Decisions (handoff snapshot)

| Date | Decision |
|------|----------|
| 2026-05-25 | Allowlist in DB; all 3 providers v1; Sonar research; OpenRouter LLM; worker from v1 |
| 2026-05-25 | 14 onboarding questions; Telegram `ru`/`rus` → Russian UI before onboarding |
| 2026-05-25 | Research/cover toggles at `/new` setup; research default from onboarding `web_research` answer |
| 2026-05-26 | **Provider setup** after personality onboarding; command **`/providers`** only (no `/connect`) |
| 2026-05-26 | **`/new` gate:** **setup complete** = profile ready + ≥1 active provider connection (not all three required) |
| 2026-05-26 | **`/new` setup:** **session destinations** = subset of connected providers only; publish never targets unconnected providers |
| 2026-05-26 | After onboarding completes → bot **auto-shows** `/providers` UI (no “type /providers” step) |
| 2026-05-26 | **Provider setup deferred:** “Skip for now” allowed; `/new` blocked until ≥1 connection; `/profile` `/settings` `/providers` still work |
| 2026-05-26 | **`/new` destinations default:** all connected providers ON; toggle off per session |
| 2026-05-26 | **Disconnect:** inline button + confirm on `/providers`; `/disconnect <provider>` shortcut |
| 2026-05-26 | **Telegram link:** reject forward unless bot is admin in target chat (`getChatMember`) |
| 2026-05-26 | **`/new` setup:** if only 1 connected provider → no destination toggles (implicit); 2+ → toggle UI |
| 2026-05-26 | **OAuth done:** Telegram DM on callback + HTML confirmation page in browser |

See `docs/adr/` for rationale.
