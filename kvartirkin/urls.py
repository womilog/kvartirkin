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
    path('ai/', include('common.ai_assistant.urls')),
    path('', include('apartments.urls')),
    path('', include('users.urls')),
]

# Serve user-uploaded media files. In a small single-container deployment we
# let Django/WhiteNoise-adjacent view serve them. For high traffic put nginx
# in front and serve MEDIA_ROOT directly instead.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
