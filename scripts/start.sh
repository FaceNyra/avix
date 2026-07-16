#!/usr/bin/env sh
set -eu

ROLE="${APP_ROLE:-api}"

python scripts/wait-for-services.py

if [ "$ROLE" = "api" ]; then
  echo "Running migrations..."
  alembic upgrade head
fi

case "$ROLE" in
  api)
    exec python -m app.main api
    ;;
  bot)
    exec python -m app.main bot
    ;;
  worker)
    exec python -m app.main worker
    ;;
  *)
    echo "Unknown APP_ROLE: $ROLE"
    exit 1
    ;;
esac
