# ---------------------------------------------------------------------------
# Kvartirkin - production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# Python behaves better in containers with these:
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: build tools for any wheels + libpq (kept lean).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first for better layer caching.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the project.
COPY . .

# Entrypoint runs migrations + collectstatic, then starts gunicorn.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
