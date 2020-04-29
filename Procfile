release: python manage.py migrate --noinput
web: gunicorn -c gunicorn/conf.py data.wsgi --log-file - --timeout=55
celeryworker: celery worker -A data -l info -Q celery
