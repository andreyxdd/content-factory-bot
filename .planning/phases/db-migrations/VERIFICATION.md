# Verification criteria — db-migrations phase

Karpathy-style loop: one falsifiable check per slice; no slice done without fresh command output.

| Slice | Success criterion | Command / test |
|-------|-------------------|----------------|
| 1 Ops | `backup-db.sh` syntactically valid; deploy README mentions backup + migrate | `bash -n deploy/scripts/backup-db.sh`; `rg backup-db deploy/README.md` |
| 2 `ensure_schema` | Default skips DDL; `AUTO_CREATE_TABLES=true` runs `create_tables` once | `pytest tests/test_schema.py -k ensure_schema -q` |
| 3 `cfbot-migrate` | Config resolves repo `alembic/`; `upgrade head` invoked | `pytest tests/test_schema.py -k migrate -q` |
| 4 Baseline parity | Alembic creates exactly `Base.metadata` tables | `pytest tests/test_schema.py -k metadata_tables -q` |
| 5 Integration | Fresh Postgres: `upgrade head` twice (idempotent); `alembic_version` at `20260525_0001` | `pytest tests/test_schema.py -m integration -q` |
| 6 API boot | Lifespan calls `ensure_schema`, not `create_tables` | `pytest tests/test_schema.py -k lifespan -q` |
| 7 Regression | Full unit suite green | `pytest -m "not integration" -q` |
