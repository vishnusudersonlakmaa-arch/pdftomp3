web: gunicorn your_project.wsgi --bind 0.0.0.0:$PORT --workers 2
worker: celery -A your_project worker --loglevel=info --concurrency=2
