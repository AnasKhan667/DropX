"""
Test settings.

Loads everything from base.py and overrides for the test runner:
- In-memory SQLite (fast, isolated per test run)
- Fast password hasher (MD5 — only safe because passwords are throwaway)
- InMemory channel layer (no Redis)
- PASSWORD_HASHERS override so tests run fast
"""

from .base import *  # noqa: F401, F403

DEBUG = False

# In-memory database — wiped on every test run, much faster than file SQLite.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Fast password hasher — tests don't care about real security.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# InMemory channel layer for WebSocket tests.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
