#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Making migrations..."
python manage.py makemigrations --noinput || true
python manage.py makemigrations users --noinput || true
python manage.py makemigrations recipes --noinput || true

echo "Running migrations..."
python manage.py migrate users --noinput || true
python manage.py migrate recipes 0001_initial --noinput || true
python manage.py migrate users 0002_user_avatar --noinput || true
python manage.py migrate recipes --noinput || true
python manage.py migrate --noinput || true

echo "Importing ingredients..."
python manage.py import_ingredients || echo "Ingredients import failed or already imported"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec "$@"