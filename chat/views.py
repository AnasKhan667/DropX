from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from notification.models import Notification
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from DropX.permissions import IsSender, IsVerifiedDriver
from delivery.models import Delivery
from accounts.models import CustomUser
from django.shortcuts import get_object_or_404

class ChatRoomListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.role.lower() == 'sender':
            return ChatRoom.objects.filter(delivery__sender_id=user)
        elif user.role.lower() == 'driver':
            return ChatRoom.objects.filter(delivery__driver_id=user)
        return ChatRoom.objects.none()

    def perform_create(self, serializer):
        delivery = Delivery.objects.get(delivery_id=serializer.validated_data['delivery']['delivery_id'])
        if self.request.user not in [delivery.sender_id, delivery.driver_id]:
            raise PermissionDenied("You must be part of the delivery.")
        serializer.save()

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        chat_room_id = self.request.query_params.get('chat_room_id')
        if not chat_room_id:
            return Message.objects.none()
        try:
            chat_room = ChatRoom.objects.get(chat_room_id=chat_room_id)
            user = self.request.user
            if user not in [chat_room.delivery.sender_id, chat_room.delivery.driver_id]:
                return Message.objects.none()
            return Message.objects.filter(chat_room=chat_room).order_by('created_at')
        except ChatRoom.DoesNotExist:
            return Message.objects.none()

    def perform_create(self, serializer):
        chat_room_id = serializer.validated_data['chat_room']['chat_room_id']
        chat_room = ChatRoom.objects.get(chat_room_id=chat_room_id)
        user = self.request.user
        if user not in [chat_room.delivery.sender_id, chat_room.delivery.driver_id]:
            raise PermissionDenied("You must be part of the delivery.")
        receiver_id = serializer.validated_data.get('receiver_id')
        receiver = CustomUser.objects.get(id=receiver_id) if receiver_id else None
        serializer.save(
            sender=user,
            receiver=receiver,
            chat_room=chat_room
        )
        # Send notification to receiver if set, else to the other participant
        notify_user = receiver if receiver else (chat_room.delivery.driver_id if user == chat_room.delivery.sender_id else chat_room.delivery.sender_id)
        Notification.objects.create(
            user_id=notify_user.id,
            delivery_id=chat_room.delivery,
            type='New Message',
            message=f'New message in chat for delivery {chat_room.delivery.delivery_id}.',
            created_at=timezone.now()
        )

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'message_id'

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(chat_room__delivery__sender_id=user) | Message.objects.filter(chat_room__delivery__driver_id=user)

class MarkMessageAsReadView(APIView):
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def post(self, request, message_id):
        message = get_object_or_404(Message, message_id=message_id)
        if request.user != message.receiver and message.receiver is not None:
            return Response({'error': 'You can only mark messages as read if you are the receiver'}, status=status.HTTP_403_FORBIDDEN)
        message.is_read = True
        message.save()
        # Mark related notifications as read
        Notification.objects.filter(
            user_id=request.user.id,
            delivery_id=message.chat_room.delivery,
            type='New Message',
            is_read=False
        ).update(is_read=True)
        return Response({'message': 'Message marked as read'}, status=status.HTTP_200_OK)