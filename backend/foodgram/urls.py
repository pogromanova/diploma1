import logging
from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from api.views.recipes import redirect_short_link

logger = logging.getLogger(__name__)

api_patterns = [
    path('', include('api.urls')),
]

url_config = [
    path('admin/', admin.site.urls),
    path('api/', include(api_patterns)),
    path('s/<str:short_id>/', redirect_short_link, name='short_link'),
]

urlpatterns = url_config

logger.info(f"Основные URL-маршруты настроены: {len(urlpatterns)} маршрутов")

if settings.DEBUG:
    media_patterns = static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += media_patterns