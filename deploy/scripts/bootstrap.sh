#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/content-factory-bot
DB_NAME=content_factory
DB_USER=cfbot

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git nginx postgresql redis-server certbot python3-certbot-nginx \
  python3-venv python3-pip rsync

install -d -m 755 "$APP_DIR"

if [[ -f "$APP_DIR/deploy/postgres/cfbot-small.conf" ]]; then
  install -m 644 "$APP_DIR/deploy/postgres/cfbot-small.conf" \
    /etc/postgresql/16/main/conf.d/cfbot-small.conf
  systemctl restart postgresql
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
  DB_PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)"
  sudo -u postgres createuser "$DB_USER"
  sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
  sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
  echo "Created PostgreSQL user $DB_USER — set DATABASE_URL in $APP_DIR/.env"
  echo "postgresql+asyncpg://${DB_USER}:${DB_PASS}@127.0.0.1:5432/${DB_NAME}"
fi

REDIS_CONF=/etc/redis/redis.conf
if grep -q '^bind 127.0.0.1' "$REDIS_CONF"; then
  :
elif grep -q '^bind ' "$REDIS_CONF"; then
  sed -i 's/^bind .*/bind 127.0.0.1 ::1/' "$REDIS_CONF"
fi
systemctl enable --now postgresql redis-server nginx

for unit in content-factory-bot content-factory-api content-factory-worker; do
  install -m 644 "$APP_DIR/deploy/systemd/${unit}.service" "/etc/systemd/system/${unit}.service"
done
systemctl daemon-reload

install -m 644 "$APP_DIR/deploy/nginx/content-bot.andreyxdd.dev.conf" \
  /etc/nginx/sites-available/content-bot.andreyxdd.dev
ln -sf /etc/nginx/sites-available/content-bot.andreyxdd.dev /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "Bootstrap done. Configure $APP_DIR/.env then:"
echo "  cd $APP_DIR && python3 -m venv .venv && .venv/bin/pip install -e ."
echo "  systemctl enable --now content-factory-bot content-factory-api content-factory-worker"
