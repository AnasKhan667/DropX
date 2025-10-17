from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_uuid>[0-9a-fA-F-]+)/?$', consumers.ChatConsumer.as_asgi()),
]
