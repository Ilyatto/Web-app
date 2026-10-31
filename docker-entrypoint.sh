#!/bin/sh
set -e
python manage.py migrate --noinput
# демо-данные только если SEED_DEMO=1
if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed
  python manage.py demo
fi
exec "$@"
