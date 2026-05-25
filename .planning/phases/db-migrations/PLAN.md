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
| 6 | TDD pins in `tests/test_schema.py` + `VERIFICATION.md` | done |

## Decisions

- **Async Alembic** via `asyncpg` (no extra sync driver).
- **Prod default:** `AUTO_CREATE_TABLES=false`; schema from `cfbot-migrate` / `alembic upgrade head`.
- **Tests:** keep fixture `Base.metadata.create_all` (unchanged).
- **Existing prod DB** created by old `create_all`: `pg_dump` then `alembic stamp head` if `\d` matches baseline.

## Verification

See [VERIFICATION.md](./VERIFICATION.md). Full gate:

```bash
docker run -d --name cfbot-test-pg -e POSTGRES_USER=cfbot -e POSTGRES_PASSWORD=cfbot \
  -e POSTGRES_DB=content_factory_test -p 5433:5432 postgres:16-alpine
pytest tests/test_schema.py -m "not integration" -q
pytest tests/test_schema.py -m integration -q
pytest -m "not integration" -q
bash -n deploy/scripts/backup-db.sh
```

## Non-goals

- Data migrations / backfills (schema only).
- CI migration job (optional follow-up).
