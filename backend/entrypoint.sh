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
python manage.py migrate recipes --noinput || true
python manage.py migrate --noinput || true

echo "Creating superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@admin.com').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
EOF

echo "Creating test data..."
python manage.py shell <<EOF
from recipes.models import Tag, Ingredient
from users.models import User

tags = [
    {'name': 'Завтрак', 'color': '#FF5733', 'slug': 'breakfast'},
    {'name': 'Обед', 'color': '#33FF57', 'slug': 'lunch'},
    {'name': 'Ужин', 'color': '#3357FF', 'slug': 'dinner'},
    {'name': 'Десерт', 'color': '#FF33F5', 'slug': 'dessert'},
]
for tag_data in tags:
    Tag.objects.get_or_create(**tag_data)

if not User.objects.filter(email='test@test.com').exists():
    user = User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpassword',
        first_name='Test',
        last_name='User'
    )

if not Ingredient.objects.exists():
    Ingredient.objects.bulk_create([
        Ingredient(name='Мука', measurement_unit='г'),
        Ingredient(name='Сахар', measurement_unit='г'),
        Ingredient(name='Яйцо', measurement_unit='шт'),
    ])
EOF

echo "Importing ingredients (if needed)..."
python manage.py import_ingredients || echo "Ingredients import skipped"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"