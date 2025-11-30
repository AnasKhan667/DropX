from django.urls import path
from .views import ChatRoomListCreateView, MessageListCreateView, MessageDetailView, MarkMessageAsReadView, ImageMessageCreateView

app_name = 'chat'

urlpatterns = [
    path('rooms/', ChatRoomListCreateView.as_view(), name='chat-room-list-create'),
    path('rooms/<uuid:chat_room_id>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('rooms/<uuid:chat_room_id>/messages/image/', ImageMessageCreateView.as_view(), name='image-message-create'),
    path('messages/<uuid:message_id>/', MessageDetailView.as_view(), name='message-detail'),
    path('messages/<uuid:message_id>/read/', MarkMessageAsReadView.as_view(), name='message-mark-read'),
]
