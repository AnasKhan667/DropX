from rest_framework import serializers
from .models import Route
from delivery.models import Delivery

class RouteSerializer(serializers.ModelSerializer):
    delivery_id = serializers.UUIDField(source="delivery_id.delivery_id", read_only=True)
    delivery_id_uuid = serializers.UUIDField(write_only=True)

    class Meta:
        model = Route
        fields = [
            'route_id',
            'delivery_id',
            'delivery_id_uuid',
            'distance',
            'path',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'route_id',
            'delivery_id',
            'distance',
            'path',
            'created_at',
            'updated_at'
        ]

    def validate_delivery_id_uuid(self, value):
        from delivery.models import Delivery
        if not Delivery.objects.filter(delivery_id=value).exists():
            raise serializers.ValidationError("Delivery does not exist.")
        return value
