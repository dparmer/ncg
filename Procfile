web: gunicorn ncg.wsgi --log-file -
worker: celery -A confidence worker -l info -B
