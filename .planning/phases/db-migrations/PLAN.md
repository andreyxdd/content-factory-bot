# Phase — Database migrations (Alembic)

## Goal

Replace boot-time `create_tables()` with versioned Alembic migrations; document Postgres backup before first prod boot and before every schema deploy.

## Slices

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `deploy/README.md` Database section + `deploy/scripts/backup-db.sh` | done |
| 2 | `alembic/` baseline revision + `cfbot-migrate` | done |
| 3 | Boot: `ensure_schema()` + `AUTO_CREATE_TABLES` (dev only) | done |
| 4 | Deploy: migrate before `systemctl restart` | done |
| 5 | `GAPS.md`, `continue.md`, ADR-0012 | done |

## Decisions

- **Async Alembic** via `asyncpg` (no extra sync driver).
- **Prod default:** `AUTO_CREATE_TABLES=false`; schema from `cfbot-migrate` / `alembic upgrade head`.
- **Tests:** keep fixture `Base.metadata.create_all` (unchanged).
- **Existing prod DB** created by old `create_all`: `pg_dump` then `alembic stamp head` if `\d` matches baseline.

## Verification

```bash
docker compose up -d postgres
cfbot-migrate   # or: .venv/bin/alembic upgrade head
pytest -m "not integration" -q
```

## Non-goals

- Data migrations / backfills (schema only).
- CI migration job (optional follow-up).
