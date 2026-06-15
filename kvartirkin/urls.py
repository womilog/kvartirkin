"""
URL configuration for kvartirkin project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.admin_site import custom_admin_site
import apartments.admin  # noqa: F401 — registers models with custom_admin_site
import users.admin      # noqa: F401 — registers models with custom_admin_site

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('', include('apartments.urls')),
    path('', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
