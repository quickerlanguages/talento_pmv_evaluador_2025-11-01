#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
export DJANGO_DEBUG="${DJANGO_DEBUG:-1}"
exec python manage.py runserver 127.0.0.1:8000
