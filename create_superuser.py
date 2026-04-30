import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kvartirkin.settings')
django.setup()

from users.models import CustomUser

# Create superuser
u, created = CustomUser.objects.get_or_create(
    phone='+79001234567',
    defaults={
        'first_name': 'Admin',
        'last_name': 'User',
        'is_staff': True,
        'is_superuser': True,
    }
)

if created:
    u.set_password('admin123')
    u.save()
    print(f'Superuser created: {u.phone}')
else:
    u.set_password('admin123')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print(f'Superuser updated: {u.phone}')

print(f'Is superuser: {u.is_superuser}')
print(f'Is active: {u.is_active}')