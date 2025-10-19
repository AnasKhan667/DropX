from rest_framework import serializers
from .models import ChatRoom, Message
from delivery.models import Delivery
from accounts.serializers import CustomUserSerializer

class ChatRoomSerializer(serializers.ModelSerializer):
    delivery_id = serializers.UUIDField(write_only=True, source='delivery.delivery_id')  # For creation

    class Meta:
        model = ChatRoom
        fields = ['chat_room_id', 'delivery', 'delivery_id', 'created_at']
        read_only_fields = ['chat_room_id', 'created_at']

    def create(self, validated_data):
        delivery_id = validated_data.pop('delivery')['delivery_id']
        delivery = Delivery.objects.get(delivery_id=delivery_id)
        return ChatRoom.objects.create(delivery=delivery)

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.UUIDField(source='sender.id', read_only=True)
    receiver = CustomUserSerializer(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)
    # is_read automatically backend handle kare
    class Meta:
        model = Message
        fields = ['message_id', 'sender_id', 'receiver', 'content', 'image', 'is_read', 'created_at']
        read_only_fields = ['message_id', 'sender_id', 'receiver', 'created_at', 'is_read']
