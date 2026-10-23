FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m app && chown -R app /app
USER app
EXPOSE 8000
# Run migrations, idempotent seed, then serve.
CMD ["sh", "-c", "alembic upgrade head && python -m app.cli seed > /dev/null && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
