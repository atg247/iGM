web: gunicorn wsgi:app --config gunicorn.conf.py
release: flask --app wsgi db upgrade
