#!/bin/bash -xe
cd /app
python manage.py migrate --noinput
python manage.py create_missing_hvcs
gunicorn -c gunicorn/conf.py data.wsgi --log-file - --access-logfile - --workers=$(nproc --all) --bind=0.0.0.0
