import django
from django.conf import settings


def pytest_configure(config):
    """Ensure Django is configured before test collection."""
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.test')
