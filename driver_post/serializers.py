from rest_framework import serializers
from .models import DriverPost, City, PostLog
from accounts.serializers import CustomUserSerializer
from vehicle.serializers import VehicleSerializer
from django.utils import timezone
from django.core.exceptions import ValidationError

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['city_id', 'name', 'state', 'country', 'latitude', 'longitude']

class PostLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLog
        fields = ['log_id', 'post', 'action', 'comments', 'timestamp']
        read_only_fields = ['log_id', 'timestamp']

class DriverPostSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    start_city = CitySerializer(read_only=True)
    end_city = CitySerializer(read_only=True)
    start_city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source='start_city', write_only=True
    )
    end_city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source='end_city', write_only=True
    )
    logs = PostLogSerializer(many=True, read_only=True)

    class Meta:
        model = DriverPost
        fields = [
            'post_id', 'user', 'vehicle', 'start_city', 'end_city',
            'start_city_id', 'end_city_id', 'start_latitude', 'start_longitude',
            'end_latitude', 'end_longitude', 'departure_date', 'departure_time',
            'available_capacity', 'max_weight', 'status', 'created_at', 'updated_at', 'logs'
        ]
        read_only_fields = ['post_id', 'user', 'status', 'created_at', 'updated_at', 'logs']

    def validate(self, data):
        if data['available_capacity'] <= 0 or data['max_weight'] <= 0:
            raise serializers.ValidationError("Capacity and weight must be positive.")

        if data['departure_date'] < timezone.now().date():
            raise serializers.ValidationError("Departure date cannot be in the past.")

        if (data.get('start_latitude') is not None) != (data.get('start_longitude') is not None):
            raise serializers.ValidationError("Both start latitude and longitude must be provided.")

        if (data.get('end_latitude') is not None) != (data.get('end_longitude') is not None):
            raise serializers.ValidationError("Both end latitude and longitude must be provided.")

        return data