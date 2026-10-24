"""
Django settings for kvartirkin project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-kvartirkin-dev-key-change-in-production')

DEBUG =  os.environ.get("DEBUG") == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# CSRF trusted origins (needed when serving over HTTPS / a domain).
# Provide as comma-separated full origins, e.g. "https://example.com,https://www.example.com"
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

INSTALLED_APPS = [
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'users',
    'apartments',
    'django_extensions',
    'common.ai_assistant',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves static files efficiently in production without a
    # separate web server. Must be placed right after SecurityMiddleware.
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
# DATABASES = {
#     'default': {
#         'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
#         # In Docker we mount a persistent /app/data directory and point the
#         # SQLite file there (see docker-compose.yml). Locally it falls back
#         # to db.sqlite3 in the project root.
#         'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
#         'USER': os.environ.get('DB_USER', ''),
#         'PASSWORD': os.environ.get('DB_PASSWORD', ''),
#         'HOST': os.environ.get('DB_HOST', ''),
#         'PORT': os.environ.get('DB_PORT', ''),
#     }
# }

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

# WhiteNoise storage: compresses static files and adds cache-busting hashes.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

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

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.yandex.ru')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'noreply@kvartirkin.local'
SERVER_EMAIL = EMAIL_HOST_USER or 'noreply@kvartirkin.local'

# Email of the landlord / administrator that receives booking requests.
# Change this default to update the address site-wide, or override it
# via the LANDLORD_EMAIL environment variable in production.
LANDLORD_EMAIL = os.environ.get('LANDLORD_EMAIL', '')

# ---------------------------------------------------------------------------
# Production security settings
# ---------------------------------------------------------------------------
# These are only enforced when DEBUG is False so local development is easy.
if not DEBUG:
    # Tell Django it's behind a proxy terminating TLS (nginx / reverse proxy).
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Redirect all HTTP to HTTPS. Set SECURE_SSL_REDIRECT=False via env
    # if you terminate TLS elsewhere or run plain HTTP behind a proxy.
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'

    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
    CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True') == 'True'

    # HTTP Strict Transport Security. Start small, raise once you're sure.
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'