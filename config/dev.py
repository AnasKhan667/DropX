"""
Development settings.

Loads everything from base.py and overrides for local development:
- DEBUG on
- CORS wide open (you trust your own browser in dev)
- InMemory channel layer so Redis isn't required
"""

from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# In dev, skip the Redis requirement — uses in-process channel layer.
# (CHANNEL_LAYERS is also overridable via USE_REDIS=false in .env, but this
# guarantees it even if someone forgets the env var.)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# CORS — only your frontend in dev. Update before shipping.
CORS_ALLOW_ALL_ORIGINS = True

# Print emails to console so you can see them without setting up SMTP.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
