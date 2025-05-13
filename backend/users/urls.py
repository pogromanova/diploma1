from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')

# Дополнительные маршруты для аватаров
avatar_urls = [
    path('users/me/avatar/', CustomUserViewSet.as_view({
        'put': 'avatar',
        'delete': 'avatar'
    }), name='user-avatar'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(avatar_urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]