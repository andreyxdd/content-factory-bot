#!/usr/bin/env bash
# Run on VPS. Uses CF_BOT_TOKEN / CF_ALLOWLIST_IDS from environment, or /root/.cfbot-secrets.
set -euo pipefail

APP_DIR=/opt/content-factory-bot
SECRETS_FILE=/root/.cfbot-secrets

if [[ -f "$SECRETS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
fi

: "${CF_BOT_TOKEN:=${BOT_TOKEN:-}}"
: "${CF_ALLOWLIST_IDS:=${ALLOWLIST_TELEGRAM_IDS:-}}"

if [[ -z "${CF_BOT_TOKEN}" && -f /root/.cfbot-bot-token ]]; then
  CF_BOT_TOKEN="$(tr -d '[:space:]' </root/.cfbot-bot-token)"
fi

if [[ -z "${CF_ALLOWLIST_IDS}" && -f /root/.hermes/.env ]]; then
  CF_ALLOWLIST_IDS="$(grep '^TELEGRAM_ALLOWED_USERS=' /root/.hermes/.env | cut -d= -f2- | cut -d, -f1)"
fi

if [[ -z "${OPENROUTER_API_KEY:-}" && -f /root/.hermes/.env ]]; then
  OPENROUTER_API_KEY="$(grep '^OPENROUTER_API_KEY=' /root/.hermes/.env | cut -d= -f2-)"
fi

DB_URL_FILE=/root/.cfbot-database-url
if [[ -f "$DB_URL_FILE" ]]; then
  DATABASE_URL="$(cat "$DB_URL_FILE")"
else
  echo "Missing $DB_URL_FILE (run bootstrap first)" >&2
  exit 1
fi

OAUTH_SECRET="$(openssl rand -hex 32)"
CRED_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null || openssl rand -base64 32)"

cat >"$APP_DIR/.env" <<EOF
BOT_TOKEN=${CF_BOT_TOKEN:-}
ALLOWLIST_TELEGRAM_IDS=${CF_ALLOWLIST_IDS}
DATABASE_URL=${DATABASE_URL}
REDIS_URL=redis://127.0.0.1:6379/0
LOG_LEVEL=INFO
PUBLIC_BASE_URL=https://content-bot.andreyxdd.dev
OAUTH_STATE_SECRET=${OAUTH_SECRET}
USE_WORKER=true
CREDENTIALS_ENCRYPTION_KEY=${CRED_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_RESEARCH=perplexity/sonar-pro
LLM_MODEL_RESEARCH_FALLBACK=perplexity/sonar
LLM_MODEL_DRAFT=anthropic/claude-sonnet-4
LLM_MODEL_DRAFT_FALLBACK=openai/gpt-4o
LLM_MODEL_FAST=google/gemini-2.5-flash
LLM_MODEL_FAST_FALLBACK=openai/gpt-4o-mini
LLM_MODEL_REVIEW=openai/gpt-4o
LLM_MODEL_REVIEW_FALLBACK=anthropic/claude-sonnet-4
LLM_MODEL_IMAGE=black-forest-labs/flux-1.1-pro
LLM_MODEL_IMAGE_FALLBACK=openai/dall-e-3
EOF
chmod 600 "$APP_DIR/.env"
echo "Wrote $APP_DIR/.env"
