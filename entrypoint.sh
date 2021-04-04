#!/bin/bash
echo "Makemigrations"
python pumps/manage.py makemigrations --noinput

echo "Migrate"
python pumps/manage.py migrate --noinput

echo "create cache table"
python pumps/manage.py createcachetable

echo "Creating superuser"
echo $DJANGO_SUPERUSER_USERNAME
python pumps/manage.py createsuperuser \
    --noinput \
    --username $DJANGO_SUPERUSER_USERNAME \
    --email $DJANGO_SUPERUSER_EMAIL

echo "Starting server"
python pumps/manage.py runserver 0.0.0.0:8080
# and add this at the end
exec "$@"