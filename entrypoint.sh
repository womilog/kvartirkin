#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Optionally load initial fixture data on first boot.
# Set LOAD_FIXTURES=1 in the environment to enable.
if [ "$LOAD_FIXTURES" = "1" ]; then
    echo "Loading initial fixtures..."
    python manage.py loaddata apartments/fixtures/initial_data.json || true
fi

echo "Starting gunicorn..."
exec gunicorn kvartirkin.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout ${GUNICORN_TIMEOUT:-60}
