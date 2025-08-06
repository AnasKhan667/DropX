from rest_framework import serializers
from .models import Chat
from accounts.models import CustomUser
from delivery.models import Delivery

class ChatSerializer(serializers.ModelSerializer):
    sender_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    receiver_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    delivery_id = serializers.PrimaryKeyRelatedField(queryset=Delivery.objects.all())

    class Meta:
        model = Chat
        fields = [
            'chat_id',
            'sender_id',
            'receiver_id',
            'delivery_id',
            'message',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['chat_id', 'created_at']
