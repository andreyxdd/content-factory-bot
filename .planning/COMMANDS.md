# Bot commands — catalog and rationale

Telegram commands are the stable entry points; inline keyboards handle branching inside flows.

## Core (implement)

| Command | Purpose |
|---------|---------|
| `/start` | Allowlist check → welcome → route to onboarding or main menu |
| `/new` | Start **content session** (blocked until personality profile ready) |
| `/sessions` | List **content sessions** by title; inline resume |
| `/onboarding` | (Re)run **onboarding session**; warns if profile overwrite |
| `/providers` | View/connect/disconnect **provider connections** |
| `/profile` | List **profile answers**; tap to re-answer one question (3+1); toggles for **web research default** and **review step** |
| `/settings` | **Primary language** (`en`/`ru`); future: notification prefs |
| `/cancel` | Abort active FSM (onboarding or content session) with confirm |
| `/help` | Command list + link to operator docs |

## Strongly recommended (v1)

| Command | Purpose |
|---------|---------|
| `/status` | Current session state, draft round number, connected providers |
| `/rename` | Change **session title** for active or last session |
| `/disconnect <provider>` | Shortcut under `/providers` |
| `/export` | Export profile + session history (GDPR-style portability) |
| `/delete_session` | Soft-delete a session with confirm |

## v2 / operator

| Command | Purpose |
|---------|---------|
| `/research` | Pull trend brief into new session (maps Research Agent) |
| `/schedule` | Opt-in daily pipeline push (maps scheduled CF) |
| `/admin_allowlist` | Operator-only: add/remove ids (if not env-file only) |
| `/admin_stats` | Usage, token spend, publish success rate |

## Commands deliberately omitted

| Idea | Why skip |
|------|----------|
| `/edit` without session context | Ambiguous; use inline menus inside session |
| `/post` | Collapses into publish step of `/new` flow |
| `/settings` as mega-command | Split into `/profile`, `/providers`, `/onboarding` |

## Menu vs command policy

- **Commands** = global navigation and escape hatches (`/cancel`, `/sessions`).
- **Inline keyboards** = all option picking (3 + custom reply pattern).
- **Reply keyboard** = avoid persistent custom keyboards (clutter); optional only for "Send contact" OAuth flows.

## Callback data conventions (implementation)

- Prefix: `ob:` onboarding, `cs:` content session, `pv:` providers
- Include `session_id` in callbacks after session created
- Version byte in payload for safe deploys
