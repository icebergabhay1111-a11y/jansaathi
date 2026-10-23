FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m app && chown -R app /app
USER app
EXPOSE 8000
# Migrate, seed an empty DB, optional admin from env, then serve.
CMD ["sh", "-c", "python -m app.cli bootstrap && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
