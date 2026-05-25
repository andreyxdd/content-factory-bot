# Instagram and LinkedIn connect via hosted OAuth (FastAPI)

Creators connect Meta and LinkedIn outside Telegram: `/providers` shows an inline URL button to `{PUBLIC_BASE_URL}/oauth/{provider}/start?telegram_user_id=…`, browser completes OAuth, callback handler on the same host stores encrypted tokens in `provider_connections`. Manual token paste in chat was rejected (leak risk, no refresh flow). An admin-only panel was rejected because Creators must self-serve connect in v1.

**Prerequisite:** Operator configures `PUBLIC_BASE_URL` (HTTPS) and provider app redirect URIs to match `/oauth/*/callback` paths documented in `.planning/OAUTH-SETUP.md`.
