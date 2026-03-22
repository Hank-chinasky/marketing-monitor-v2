#!/usr/bin/env sh
set -eu

mkdir -p /app/data /app/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn marketing_monitor.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
