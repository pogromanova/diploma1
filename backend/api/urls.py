from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.recipes import RecipeViewSet, IngredientViewSet, TagViewSet
from .views.users import UserViewSet  

import logging
logger = logging.getLogger(__name__)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('users', UserViewSet, basename='users')

for route in router_v1.urls:
    logger.info(f"Registered route: {route}")

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]

logger.info(f"API URL patterns: {urlpatterns}")