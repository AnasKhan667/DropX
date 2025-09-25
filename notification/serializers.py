from rest_framework import serializers
from .models import Notification
from accounts.serializers import CustomUserSerializer
from delivery.serializers import DeliveryReadSerializer

class NotificationSerializer(serializers.ModelSerializer):
    user_id = CustomUserSerializer(read_only=True)
    delivery_id = DeliveryReadSerializer(read_only=True)
    # For manual creation (if needed)
    user_id_id = serializers.UUIDField(write_only=True, required=False)
    delivery_id_id = serializers.UUIDField(write_only=True, allow_null=True, required=False)

    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'user_id',
            'user_id_id',
            'delivery_id',
            'delivery_id_id',
            'type',
            'message',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['notification_id', 'created_at', 'user_id', 'delivery_id']

    def validate(self, data):
        if 'user_id_id' in data:
            from accounts.models import CustomUser
            if not CustomUser.objects.filter(id=data['user_id_id']).exists():
                raise serializers.ValidationError("Invalid user_id.")
        if 'delivery_id_id' in data and data['delivery_id_id']:
            from delivery.models import Delivery
            if not Delivery.objects.filter(delivery_id=data['delivery_id_id']).exists():
                raise serializers.ValidationError("Invalid delivery_id.")
        return data