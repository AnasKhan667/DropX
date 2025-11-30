from rest_framework import serializers
from .models import ChatRoom, Message
from delivery.models import Delivery
from accounts.serializers import CustomUserSerializer


class DeliveryBriefSerializer(serializers.Serializer):
    """Brief delivery info for chat room list"""
    delivery_id = serializers.UUIDField()
    pickup_city = serializers.SerializerMethodField()
    dropoff_city = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()
    status = serializers.CharField()

    def get_pickup_city(self, obj):
        if obj.pickup_city:
            return {'city_id': str(obj.pickup_city.city_id), 'name': obj.pickup_city.name}
        return None

    def get_dropoff_city(self, obj):
        if obj.dropoff_city:
            return {'city_id': str(obj.dropoff_city.city_id), 'name': obj.dropoff_city.name}
        return None

    def get_sender(self, obj):
        if obj.sender_id:
            return {
                'id': str(obj.sender_id.id),
                'first_name': obj.sender_id.first_name,
                'last_name': obj.sender_id.last_name,
                'phone_number': str(obj.sender_id.phone_number) if obj.sender_id.phone_number else None,
            }
        return None

    def get_driver(self, obj):
        # Check driver_id first, then driver_post_id
        driver = None
        if obj.driver_id:
            driver = obj.driver_id
        elif obj.driver_post_id:
            driver = obj.driver_post_id.user
        
        if driver:
            return {
                'id': str(driver.id),
                'first_name': driver.first_name,
                'last_name': driver.last_name,
                'phone_number': str(driver.phone_number) if driver.phone_number else None,
            }
        return None


class ChatRoomSerializer(serializers.ModelSerializer):
    delivery_id = serializers.UUIDField(write_only=True, source='delivery.delivery_id')  # For creation
    delivery_details = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['chat_room_id', 'delivery', 'delivery_id', 'delivery_details', 'last_message', 'created_at']
        read_only_fields = ['chat_room_id', 'created_at', 'delivery_details', 'last_message']

    def get_delivery_details(self, obj):
        return DeliveryBriefSerializer(obj.delivery).data

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'content': last_msg.content,
                'created_at': last_msg.created_at.isoformat(),
                'sender_id': str(last_msg.sender.id),
                'is_read': last_msg.is_read,
            }
        return None

    def create(self, validated_data):
        delivery_id = validated_data.pop('delivery')['delivery_id']
        delivery = Delivery.objects.get(delivery_id=delivery_id)
        return ChatRoom.objects.create(delivery=delivery)

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.UUIDField(source='sender.id', read_only=True)
    receiver = CustomUserSerializer(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)
    # is_read automatically backend handle 
    class Meta:
        model = Message
        fields = ['message_id', 'sender_id', 'receiver', 'content', 'image', 'is_read', 'created_at']
        read_only_fields = ['message_id', 'sender_id', 'receiver', 'created_at', 'is_read']
