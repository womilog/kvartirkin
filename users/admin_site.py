import re
from django.contrib.admin import AdminSite
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


# Create the custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')