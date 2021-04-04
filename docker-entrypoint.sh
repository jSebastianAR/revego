#!/bin/bash
echo "Makemigrations..."
python pumps/manage.py makemigrations --noinput

echo "Migrate..."
python pumps/manage.py migrate --noinput

echo "Starting server..."
python pumps/manage.py runserver 0.0.0.0:8080 --insecure
# and add this at the end
exec "$@"