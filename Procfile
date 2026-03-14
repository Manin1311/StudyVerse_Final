web: gunicorn --worker-class gthread --threads 4 -w 1 --timeout 120 --bind 0.0.0.0:$PORT --log-level info --capture-output --error-logfile - app:app
