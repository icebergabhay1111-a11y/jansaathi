#!/bin/sh
# Container entrypoint (Render / single-container deploys).
# 1. bootstrap: migrations + seed an empty DB + optional admin — one Python process (fast cold start)
# 2. API on 127.0.0.1:8000 (internal only)
# 3. website on public $PORT, opened only after the API is healthy, so the first visitor
#    after a cold start never hits "data service unavailable"
# Exits if either server dies, so the platform restarts the container.
set -e
cd /app/backend
python -m app.cli bootstrap
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers &
API=$!
python - <<'EOF'
import sys, time, urllib.request
deadline = time.time() + 90
while time.time() < deadline:
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2)
        print("API healthy; starting website")
        sys.exit(0)
    except Exception:
        time.sleep(0.5)
sys.exit("API did not become healthy within 90s")
EOF
cd /app/frontend
node node_modules/next/dist/bin/next start -H 0.0.0.0 -p "${PORT:-10000}" &
WEB=$!
while kill -0 $API 2>/dev/null && kill -0 $WEB 2>/dev/null; do sleep 5; done
kill $API $WEB 2>/dev/null || true
exit 1
