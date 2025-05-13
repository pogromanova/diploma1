#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Making migrations..."
python manage.py makemigrations --noinput
python manage.py makemigrations users --noinput
python manage.py makemigrations recipes --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Importing ingredients..."
python manage.py import_ingredients || echo "Ingredients import failed or already imported"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec "$@"