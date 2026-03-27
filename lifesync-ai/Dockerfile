FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 (psycopg2 빌드에 필요)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

COPY . .

CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
