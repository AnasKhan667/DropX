from rest_framework import serializers
from .models import Vehicle, VehicleLog
from django.utils import timezone

class VehicleLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleLog
        fields = ['log_id', 'vehicle', 'action', 'comments', 'timestamp']  # comments retained
        read_only_fields = ['log_id', 'timestamp']


class VehicleSerializer(serializers.ModelSerializer):
    logs = VehicleLogSerializer(many=True, read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'vehicle_id',
            'vehicle_type_name',
            'description',
            'make',
            'model',
            'year',
            'number_plate',  # updated field name
            'color',
            'status',
            'created_at',
            'updated_at',
            'logs'
        ]
        read_only_fields = ['vehicle_id', 'status', 'created_at', 'updated_at', 'logs']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user

        # Auto-approve if driver is verified
        driver_profile = getattr(validated_data['user'], 'driver_profile', None)
        if driver_profile and getattr(driver_profile, 'is_driver_verified', False):
            validated_data['status'] = 'approved'
        else:
            validated_data['status'] = 'pending'

        return super().create(validated_data)

    def validate(self, data):
        year = data.get('year')
        if year and (year < 1900 or year > timezone.now().year + 1):
            raise serializers.ValidationError("Invalid vehicle year.")
        return data
