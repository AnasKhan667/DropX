from rest_framework import serializers
from .models import ChatRoom, Message
from delivery.serializers import DeliveryReadSerializer
from delivery.models import Delivery  # Assume you have this; import if needed
from accounts.serializers import CustomUserSerializer  # Assume you have this

class ChatRoomSerializer(serializers.ModelSerializer):
    delivery = DeliveryReadSerializer(read_only=True)
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
    chat_room_id = serializers.UUIDField(write_only=True, source='chat_room.chat_room_id')
    sender_id = serializers.UUIDField(source='sender.id', read_only=True)
    receiver_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)  # Optional
    receiver = CustomUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['message_id', 'chat_room_id', 'sender_id', 'receiver_id', 'receiver', 'content', 'is_read', 'created_at']
        read_only_fields = ['message_id', 'sender_id', 'created_at']