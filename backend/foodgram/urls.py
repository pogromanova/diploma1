from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.views.recipes import redirect_short_link  # Добавьте к существующим импортам

import logging
logger = logging.getLogger(__name__)

urlpatterns = [
    path('admin/', admin.site.urls),
    # УБЕДИТЕСЬ, ЧТО ЗДЕСЬ ТОЛЬКО ОДИН ПУТЬ ДЛЯ API!
    path('api/', include('api.urls')),
    path('s/<str:short_id>/', redirect_short_link, name='short_link'),
]

# Логирование для отладки маршрутизации
logger.info(f"Main URL patterns: {urlpatterns}")

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)