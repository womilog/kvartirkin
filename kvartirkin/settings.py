"""
Django settings for kvartirkin project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-kvartirkin-dev-key-change-in-production')

DEBUG =  True 
INSTALLED_APPS = [
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'users',
    'apartments',
    'django_extensions',
    'common.ai_assistant',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kvartirkin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media', # for vk logo
                'apartments.context_processors.current_year'
            ],
        },
    },
]

WSGI_APPLICATION = 'kvartirkin.wsgi.application'

# Database — PostgreSQL in production, SQLite for local dev
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Login URLs
LOGIN_URL = '/auth/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Email configuration
# ---------------------------------------------------------------------------
# In development we use the console backend so emails are printed to stdout.
# In production set EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
# and provide EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD via env vars.
# EMAIL_BACKEND = os.environ.get(
#     'EMAIL_BACKEND',
#     'django.core.mail.backends.console.EmailBackend',
# )
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.yandex.ru')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
# EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
# DEFAULT_FROM_EMAIL = os.environ.get(
#     'DEFAULT_FROM_EMAIL', 'noreply@kvartirkin.local'
# )

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'womilog228@mail.ru'
EMAIL_HOST_PASSWORD = 'wQLfc5oU63dm2H59hDeZ'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

# Email of the landlord / administrator that receives booking requests.
# Change this default to update the address site-wide, or override it
# via the LANDLORD_EMAIL environment variable in production.
LANDLORD_EMAIL = 'chop.vlad35@mail.ru'  # os.environ.get('LANDLORD_EMAIL', 'womilog228@mail.ru')