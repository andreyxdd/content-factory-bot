# Allowlist stored in PostgreSQL, seeded from env

Allowed Telegram user ids live in `allowlist_entries`, not only in environment variables. Deploy seeds ids from `ALLOWLIST_TELEGRAM_IDS`; runtime checks query the DB so operators can add or revoke access without redeploy. Env-only gating was rejected because it does not scale past a handful of creators and cannot be updated live.
