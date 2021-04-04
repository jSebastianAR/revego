#!/bin/bash
echo "Makemigrations..."
python pumps/manage.py makemigrations --noinput

echo "Migrate..."
python pumps/manage.py migrate --noinput

#Try catch if user already exist
{
    echo "Creating superuser: $DJANGO_SUPERUSER_USERNAME"
    python pumps/manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
} || {
    echo "Superuser $DJANGO_SUPERUSER_USERNAME already exists"
}

echo "Starting server..."
python pumps/manage.py runserver 0.0.0.0:8080 --insecure
# and add this at the end
exec "$@"