# Foodgram - «Продуктовый помощник»

## Описание проекта

Сервис "Фудграм" - это онлайн-платформа для публикации рецептов. Пользователи могут создавать свои рецепты, подписываться на других авторов, добавлять понравившиеся рецепты в избранное и формировать список покупок для выбранных рецептов.

## Технологии

- Python 3.9
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- GitHub Actions

## Установка и запуск проекта локально

### Предварительные требования

- Docker и Docker Compose

### Шаги по установке

1. Клонировать репозиторий:
```
git clone https://github.com/username/foodgram-project-react.git
cd foodgram-project-react/
```

2. В директории infra создать файл .env со следующим содержимым:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

3. Запустить Docker Compose:
```
cd infra
docker-compose up -d
```

4. Выполнить миграции и собрать статику:
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
```

5. Загрузить начальные данные ингредиентов:
```
docker-compose exec backend python manage.py import_ingredients data/ingredients.json
```

6. Создать суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```

7. Проект будет доступен по адресу http://localhost/

## Документация API

Документация API доступна по адресу http://localhost/api/docs/ после запуска проекта.

## CI/CD

Проект настроен на автоматический деплой при пуше в ветку main. GitHub Actions автоматически:
1. Проверяет код на соответствие стандартам PEP8
2. Собирает и публикует образы Docker на Docker Hub
3. Деплоит проект на сервер
4. Отправляет уведомление об успешном деплое

## Автор

Ваше Имя - [GitHub](https://github.com/username)