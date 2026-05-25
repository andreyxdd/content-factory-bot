# Alembic owns schema; no DDL on production boot

## Context

The API, Telegram bot, and Redis worker previously called `Base.metadata.create_all` on every start. That is fine for empty dev databases but does not version schema, cannot alter existing columns, and invites race noise when three processes start together.

## Decision

- **Alembic** is the single source of schema changes (`alembic/`, `cfbot-migrate` → `upgrade head`).
- **Production** runs migrations before `systemctl restart`; operators **backup** Postgres first (`deploy/scripts/backup-db.sh`, documented in `deploy/README.md`).
- **Boot** calls `ensure_schema()` only when `AUTO_CREATE_TABLES=true` (local dev convenience; default `false`).
- **Tests** continue to use in-fixture `create_all` on SQLite.

## Consequences

- Every model change ships with a new Alembic revision.
- Databases created by older `create_all` on prod must be baselined with `alembic stamp head` after verifying table parity, not assumed empty.
