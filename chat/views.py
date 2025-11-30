from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from notification.models import Notification
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from delivery.models import Delivery
from accounts.models import CustomUser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class ChatRoomListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.role.lower() == 'sender':
            return ChatRoom.objects.filter(delivery__sender_id=user)
        elif user.role.lower() == 'driver':
            # Check all ways a driver can be associated with a delivery
            return ChatRoom.objects.filter(
                Q(delivery__driver_id=user) |
                Q(delivery__driver_post_id__user=user) |
                Q(messages__sender=user) |
                Q(messages__receiver=user)
            ).distinct()
        return ChatRoom.objects.none()

    def perform_create(self, serializer):
        delivery = Delivery.objects.get(delivery_id=serializer.validated_data['delivery']['delivery_id'])
        if self.request.user not in [delivery.sender_id, delivery.driver_post_id.user]:
            raise PermissionDenied("You must be part of the delivery.")
        serializer.save()

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        chat_room_id = self.kwargs.get('chat_room_id') 
        if not chat_room_id:
            return Message.objects.none()
        try:
            chat_room = ChatRoom.objects.get(chat_room_id=chat_room_id)
            user = self.request.user
            delivery = chat_room.delivery
            
            # Check if user is the sender
            is_sender = user.id == delivery.sender_id.id
            
            # Check if user is the driver (via driver_id or driver_post_id)
            is_driver = (
                (delivery.driver_id and user.id == delivery.driver_id.id) or
                (delivery.driver_post_id and user.id == delivery.driver_post_id.user.id)
            )
            
            if not (is_sender or is_driver):
                return Message.objects.none()
            return Message.objects.filter(chat_room=chat_room).order_by('created_at')
        except ChatRoom.DoesNotExist:
            return Message.objects.none()

    def perform_create(self, serializer):
        chat_room_id = self.kwargs.get('chat_room_id') 
        chat_room = ChatRoom.objects.get(chat_room_id=chat_room_id)
        user = self.request.user

        if user == chat_room.delivery.sender_id:
            receiver = chat_room.delivery.driver_post_id.user 
        else:
            receiver = chat_room.delivery.sender_id

        serializer.save(
            sender=user,
            receiver=receiver,
            chat_room=chat_room
        )

        Notification.objects.create(
            user_id=receiver,
            delivery_id=chat_room.delivery,
            type='New Message',
            message=f'New message in chat for delivery {chat_room.delivery.delivery_id}.',
            created_at=timezone.now()
        )


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'message_id'

class MarkMessageAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, message_id):
        message = get_object_or_404(Message, message_id=message_id)
        if request.user != message.receiver and message.receiver is not None:
            return Response({'error': 'You can only mark messages as read if you are the receiver'}, status=status.HTTP_403_FORBIDDEN)
        message.is_read = True
        message.save()
        Notification.objects.filter(
            user_id=request.user.id,
            delivery_id=message.chat_room.delivery,
            type='New Message',
            is_read=False
        ).update(is_read=True)
        return Response({'message': 'Message marked as read'}, status=status.HTTP_200_OK)


class ImageMessageCreateView(APIView):
    """Upload an image message and broadcast via WebSocket"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, chat_room_id):
        try:
            chat_room = ChatRoom.objects.get(chat_room_id=chat_room_id)
        except ChatRoom.DoesNotExist:
            return Response({'error': 'Chat room not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        delivery = chat_room.delivery

        # Validate user is part of the chat
        is_sender = user.id == delivery.sender_id.id
        is_driver = (
            (delivery.driver_id and user.id == delivery.driver_id.id) or
            (delivery.driver_post_id and user.id == delivery.driver_post_id.user.id)
        )

        if not (is_sender or is_driver):
            return Response({'error': 'You are not part of this chat'}, status=status.HTTP_403_FORBIDDEN)

        # Get image from request
        image = request.FILES.get('image')
        content = request.data.get('content', '')

        if not image:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Determine receiver
        if is_sender:
            if delivery.driver_id:
                receiver = delivery.driver_id
            elif delivery.driver_post_id:
                receiver = delivery.driver_post_id.user
            else:
                return Response({'error': 'No driver assigned'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            receiver = delivery.sender_id

        # Create message with image
        message = Message.objects.create(
            chat_room=chat_room,
            sender=user,
            receiver=receiver,
            content=content,
            image=image,
            created_at=timezone.now()
        )

        # Create notification
        Notification.objects.create(
            user_id=receiver,
            delivery_id=delivery,
            type='New Message',
            message=f'New image message in chat for delivery {delivery.delivery_id}.',
            created_at=timezone.now()
        )

        # Build full image URL
        image_url = request.build_absolute_uri(message.image.url) if message.image else None

        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{chat_room_id}'
        
        try:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': str(message.message_id),
                    'content': content,
                    'image': image_url,
                    'sender_id': str(user.id),
                    'receiver_id': str(receiver.id),
                    'created_at': message.created_at.isoformat(),
                }
            )
            print(f"✅ Image message broadcast to group: {room_group_name}")
        except Exception as e:
            # Log error but don't fail - message is already saved
            print(f"❌ Channel layer error (Redis may not be running): {e}")

        # Return response
        return Response({
            'message_id': str(message.message_id),
            'sender_id': str(user.id),
            'receiver': {
                'id': str(receiver.id),
                'first_name': receiver.first_name,
                'last_name': receiver.last_name,
            },
            'content': content,
            'image': image_url,
            'is_read': False,
            'created_at': message.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
