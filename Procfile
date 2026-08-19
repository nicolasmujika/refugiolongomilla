release: python manage.py collectstatic --noinput
web: python manage.py migrate --noinput && gunicorn config.wsgi --log-file -