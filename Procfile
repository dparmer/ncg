web: gunicorn ncg.wsgi --log-file -
worker: celery -A confidence worker -l info
worker: celery -A confidence beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

