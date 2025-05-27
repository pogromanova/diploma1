from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views.recipes import RecipeViewSet, IngredientViewSet, TagViewSet
from api.views.users import CustomUserViewSet

import logging
logger = logging.getLogger(__name__)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('users', CustomUserViewSet, basename='users')

# Логирование зарегистрированных маршрутов
for route in router_v1.urls:
    logger.info(f"Registered route: {route}")

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

# Добавляем дополнительное логирование для отладки
logger.info(f"API URL patterns: {urlpatterns}")