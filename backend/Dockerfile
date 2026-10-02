# Backend image. Build from the project root, because the app also needs the config/ folder:
#   docker build -f backend/Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config /app/config
COPY backend /app/backend

EXPOSE 8000
# 1. create or update the tables  2. load the demo data on the first start only  3. start the API
CMD ["sh", "-c", "alembic upgrade head && (python -m seed.run || echo 'Demo data is already loaded.') && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
