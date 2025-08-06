from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatListCreateView.as_view(), name='chat-list-create'),
    path('<uuid:chat_id>/', views.ChatDetailView.as_view(), name='chat-detail'),
    path('<uuid:chat_id>/mark-as-read/', views.MarkChatAsReadView.as_view(), name='mark-chat-as-read'),
]