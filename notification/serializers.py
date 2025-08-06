from rest_framework import serializers
from .models import Notification
from accounts.models import CustomUser
from delivery.models import Delivery

class NotificationSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    delivery_id = serializers.PrimaryKeyRelatedField(queryset=Delivery.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'user_id',
            'delivery_id',
            'type',
            'message',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['notification_id', 'created_at']
