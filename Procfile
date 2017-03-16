release: python manage.py migrate --noinput
web: gunicorn -c gunicorn/conf.py data.wsgi --log-file -
