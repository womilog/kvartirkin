"""
URL configuration for kvartirkin project.
"""
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.sitemaps.views import sitemap
from users.admin_site import custom_admin_site
from apartments import robots as robots_view
from apartments.sitemaps import sitemaps

import apartments.admin  # noqa: F401 — registers models with custom_admin_site
import users.admin      # noqa: F401 — registers models with custom_admin_site

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('ai/', include('common.ai_assistant.urls')),
    path('', include('apartments.urls')),
    path('', include('users.urls')),
    # robots.txt — must be at root, served as text/plain
    path('robots.txt', robots_view.robots_txt, name='robots_txt'),
    # sitemap.xml
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

# Serve user-uploaded media files. Unlike django.conf.urls.static.static(),
# which silently does nothing when DEBUG=False, this explicit serve() route
# works in production too. For high traffic, let nginx serve /media/ directly
# (see the nginx location block) — then this route acts only as a fallback.
urlpatterns += [
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
]
