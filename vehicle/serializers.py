from rest_framework import serializers
from .models import Vehicle, VehicleType

class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['vehicle_type_id', 'type_name', 'max_capacity', 'description', 'created_at']
        read_only_fields = ['vehicle_type_id', 'created_at']

class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type = VehicleTypeSerializer()

    class Meta:
        model = Vehicle
        fields = ['vehicle_id', 'user_id', 'vehicle_type_id', 'make', 'model', 'year', 'license_plate', 'color', 'insurance', 'registration_document', 'capacity', 'is_active', 'created_at', 'updated_at', 'vehicle_type']
        read_only_fields = ['vehicle_id', 'created_at', 'updated_at']