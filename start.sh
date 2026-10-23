#!/bin/sh
# Starts the API (internal) and the website (public $PORT). Exits if either process dies,
# so the host restarts the container.
set -e
cd /app/backend
alembic upgrade head
python -m app.cli seed-if-empty
# Optional: create/refresh an admin account from env vars (Render free plan has no shell)
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then python -m app.cli create-admin "$ADMIN_EMAIL" || echo "admin account not created (check ADMIN_PASSWORD length)"; fi
uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers &
API=$!
cd /app/frontend
node node_modules/next/dist/bin/next start -H 0.0.0.0 -p "${PORT:-10000}" &
WEB=$!
# wait for whichever exits first, then stop the other
while kill -0 $API 2>/dev/null && kill -0 $WEB 2>/dev/null; do sleep 5; done
kill $API $WEB 2>/dev/null || true
exit 1
