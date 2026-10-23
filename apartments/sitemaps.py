from django.urls import reverse
from django.contrib.sitemaps import Sitemap


class StaticPagesSitemap(Sitemap):
    """Static pages: home and catalog."""
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return ["index", "apartment_list"]

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        return "weekly"

    def priority(self, item):
        return 0.9


class ApartmentSitemap(Sitemap):
    """Dynamic sitemap for active apartments."""
    priority = 0.8
    changefreq = "daily"

    def items(self):
        from apartments.models import Apartment
        return Apartment.objects.filter(is_active=True).order_by("-created_at")

    def location(self, obj):
        return reverse("apartment_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.created_at

    def changefreq(self, obj):
        return "daily"

    def priority(self, obj):
        return 0.8


sitemaps = {
    "static": StaticPagesSitemap,
    "apartments": ApartmentSitemap,
}
