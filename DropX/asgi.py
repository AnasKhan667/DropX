"""
ASGI config for DropX project.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# ✅ Django settings environment set karo pehle
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')

# ✅ Django setup abhi karo
django.setup()

# ✅ Ab import karo routing aur middleware
from chat.middleware import JWTAuthMiddleware
import chat.routing

# ✅ Application config
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(   # 👈 yahan apna custom middleware lagao
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
