from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Chat
from .serializers import ChatSerializer
from notification.models import Notification
from django.utils import timezone

class ChatListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(sender_id=user) | Chat.objects.filter(receiver_id=user)

class ChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    lookup_field = 'chat_id'

class MarkChatAsReadView(APIView):
    def post(self, request, chat_id):
        try:
            chat = Chat.objects.get(chat_id=chat_id)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user != chat.receiver_id:
            return Response({'error': 'You can only mark chats as read if you are the receiver'}, status=status.HTTP_403_FORBIDDEN)

        chat.is_read = True
        chat.save()

        # Optionally update related notifications
        Notification.objects.filter(
            user_id=chat.receiver_id,
            delivery_id=chat.delivery_id,
            type='New Message',
            is_read=False
        ).update(is_read=True)

        return Response({'message': 'Chat marked as read'}, status=status.HTTP_200_OK)