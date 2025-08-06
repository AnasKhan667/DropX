from rest_framework import serializers
from .models import Route
from delivery.models import Delivery

class RouteSerializer(serializers.ModelSerializer):
    delivery_id = serializers.PrimaryKeyRelatedField(queryset=Delivery.objects.all())

    class Meta:
        model = Route
        fields = [
            'route_id',
            'delivery_id',
            'start_location',
            'end_location',
            'waypoints',
            'distance',
            'estimated_time',
            'actual_time',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['route_id', 'created_at', 'updated_at']
