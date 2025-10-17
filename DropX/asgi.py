"""
ASGI config for DropX project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django

# ✅ Pehle settings set karo
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DropX.settings")

# ✅ Django ko setup karo
django.setup()

# ✅ Ab import karo ASGI + routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})

