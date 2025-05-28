#!/bin/sh

echo "Проверка доступности PostgreSQL..."
until nc -z $DB_HOST $DB_PORT; do
  echo "PostgreSQL недоступен - ожидание..."
  sleep 1
done
echo "PostgreSQL запущен и готов к работе"

echo "Генерация миграций..."
python manage.py makemigrations --noinput
python manage.py makemigrations recipes --noinput

echo "Применение миграций..."
python manage.py migrate recipes --noinput
python manage.py migrate --noinput

echo "Настройка учетной записи администратора..."
python manage.py shell <<PYTHON_SCRIPT
from django.contrib.auth import get_user_model
User = get_user_model()
admin_exists = User.objects.filter(email='admin@admin.com').exists()
if not admin_exists:
    User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        password='admin'
    )
    print("Администратор создан")
else:
    print("Администратор уже существует")
PYTHON_SCRIPT

echo "Инициализация тестовых данных..."
python manage.py shell <<PYTHON_SCRIPT
from recipes.models import Tag, Ingredient, User

# Создание тегов
sample_tags = [
    {'name': 'Завтрак', 'color': '#FF5733', 'slug': 'breakfast'},
    {'name': 'Обед', 'color': '#33FF57', 'slug': 'lunch'},
    {'name': 'Ужин', 'color': '#3357FF', 'slug': 'dinner'},
    {'name': 'Десерт', 'color': '#FF33F5', 'slug': 'dessert'},
]

for tag_info in sample_tags:
    Tag.objects.get_or_create(**tag_info)


PYTHON_SCRIPT

echo "Импорт полного списка ингредиентов..."
python manage.py ingredient_importer || echo "Импорт ингредиентов пропущен"

echo "Сбор статических файлов..."
python manage.py collectstatic --noinput

echo "Запуск сервера..."
exec "$@"