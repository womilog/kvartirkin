import re
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.forms import AdminAuthenticationForm


class CustomAdminAuthenticationForm(AdminAuthenticationForm):
    """Custom admin login form with phone normalization."""

    def clean_username(self):
        phone = self.cleaned_data.get('username', '')
        # Strip all non-digit characters
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11:
            # Normalize to +7XXXXXXXXXX format
            return '+7' + digits[1:]
        return phone


class CustomAdminSite(AdminSite):
    """Custom admin site with phone-based authentication."""
    login_form = CustomAdminAuthenticationForm
    site_header = 'Квартиркин - Администрирование'
    site_title = 'Квартиркин Админ'
    index_title = 'Управление'

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff


# Create the custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')


class CustomModelAdmin(ModelAdmin):
    """Base ModelAdmin that grants full access to staff users."""

    def has_module_perms(self, request, app_label=None):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff
