# Single-container image: Next.js website on $PORT + FastAPI on 127.0.0.1:8000 (proxied via /api).
# Used by render.yaml. For separate services, use backend/Dockerfile and frontend/Dockerfile instead.

FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1 BACKEND_URL=http://127.0.0.1:8000
RUN npm run build && npm prune --omit=dev

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production BACKEND_URL=http://127.0.0.1:8000
COPY --from=web /usr/local/bin/node /usr/local/bin/node
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web /app/frontend
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh && useradd -m app && chown -R app /app
USER app
EXPOSE 10000
CMD ["/app/start.sh"]
