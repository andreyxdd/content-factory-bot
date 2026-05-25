# Continue — production credentials only

## Status

Autonomous v1 (phases 0.5–4) complete on `main`. No slice handoff — run pytest before any change.

## Operator-only next steps

1. Meta + LinkedIn developer apps → real OAuth token exchange in `api/oauth.py`
2. `CREDENTIALS_ENCRYPTION_KEY` (Fernet) in production `.env`
3. `OPENROUTER_API_KEY` for live drafts/research/vision
4. `USE_WORKER=true` + `cfbot-worker` for long runs

## Verify

```bash
pytest -m "not integration" -q
```
