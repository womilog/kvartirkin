from django.http import HttpResponse


def robots_txt(request):
    """Generate robots.txt for search engines."""
    domain = request.get_host()
    content = f"""User-agent: *
Allow: /

Sitemap: https://{domain}/sitemap.xml

User-agent: Yandex
Allow: /
Host: https://{domain}

User-agent: Googlebot
Allow: /

Crawl-delay: 1
"""
    return HttpResponse(content, content_type="text/plain")
