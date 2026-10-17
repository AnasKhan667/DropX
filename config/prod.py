"""
Production settings.

Loads everything from base.py and locks down anything dangerous:
- DEBUG must be False
- ALLOWED_HOSTS must be set explicitly
- CORS restricted to known origins
- Postgres instead of SQLite
- Redis channel layer required
- Real password validators (already on, but enforced here)
"""

from .base import *  # noqa: F401, F403
from decouple import config, Csv

# Hard assertions — fail loud if these are missing in prod.
DEBUG = config('DEBUG', default=False, cast=bool)
assert not DEBUG, "DEBUG must be False in production"

SECRET_KEY = config('SECRET_KEY')
assert SECRET_KEY and SECRET_KEY != 'django-insecure-change-me', \
    "SECRET_KEY must be set to a strong value in production"

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
assert ALLOWED_HOSTS, "ALLOWED_HOSTS must be set in production"

# Postgres
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='dropx'),
        'USER': config('DB_USER', default='dropx'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# CORS — explicit allowlist
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())

# Security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Redis is required in prod
USE_REDIS = config('USE_REDIS', default='true').lower() == 'true'
assert USE_REDIS, "USE_REDIS must be true in production (InMemory channel layer does not scale)"
