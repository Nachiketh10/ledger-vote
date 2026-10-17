# --- Backend: Flask + Gunicorn ---
FROM python:3.11-slim

WORKDIR /app

# System deps needed by opencv-python-headless / mediapipe / onnxruntime
# at runtime (even the "headless" opencv build needs libgl/libglib for
# some codecs) — kept minimal, no build toolchain here since wheels are
# used for everything except insightface's native extension, which
# needs gcc/g++.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Migrations are NOT run automatically on container start — run
# `docker compose exec backend flask db upgrade` explicitly after the
# first `docker compose up`, so a schema change never applies silently
# on a routine restart.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "wsgi:app"]
