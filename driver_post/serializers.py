from rest_framework import serializers
from .models import DriverPost, City, PostLog
from accounts.serializers import CustomUserSerializer
from vehicle.models import Vehicle
from django.utils import timezone
from vehicle.serializers import VehicleSerializer

class CitySerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = City
        fields = ['city_id', 'name', 'state', 'country', 'latitude', 'longitude']
        extra_kwargs = {
            'name': {'validators': []},  # Disable unique validator
        }


class PostLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLog
        fields = ['log_id', 'post', 'action', 'comments', 'timestamp']
        read_only_fields = ['log_id', 'timestamp']

class DriverPostSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    logs = PostLogSerializer(many=True, read_only=True)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        source='vehicle',
        write_only=True,
        required=True
    )
    start_city_data = CitySerializer(write_only=True, required=True)
    end_city_data = CitySerializer(write_only=True, required=True)
    vehicle = VehicleSerializer(read_only=True) 

    class Meta:
        model = DriverPost
        fields = [
            'post_id', 'user', 'logs', 'vehicle',     # read-only
            'vehicle_id', 'start_city_data', 'end_city_data', # write-only
            'departure_date', 'departure_time',
            'available_capacity', 'max_weight',
            'start_latitude', 'start_longitude',
            'end_latitude', 'end_longitude'
        ]
        read_only_fields = ['post_id', 'logs', 'vehicle' ,'start_latitude', 'start_longitude', 'end_latitude', 'end_longitude']

    def get_user(self, obj):
        return CustomUserSerializer(obj.user).data if obj.user else None

    def create(self, validated_data):
        start_city_data = validated_data.pop("start_city_data")
        end_city_data = validated_data.pop("end_city_data")

        # Get or create start city
        start_city = City.objects.get_or_create(
            name=start_city_data["name"],
            state=start_city_data.get("state") or "",
            country=start_city_data.get("country") or "",
            defaults={
                "latitude": start_city_data.get("latitude"),
                "longitude": start_city_data.get("longitude")
            },
        )[0]

        # Get or create end city
        end_city = City.objects.get_or_create(
            name=end_city_data["name"],
            state=end_city_data.get("state") or "",
            country=end_city_data.get("country") or "",
            defaults={
                "latitude": end_city_data.get("latitude"),
                "longitude": end_city_data.get("longitude")
            },
        )[0]

        validated_data["start_city"] = start_city
        validated_data["end_city"] = end_city
        validated_data["start_latitude"] = start_city.latitude
        validated_data["start_longitude"] = start_city.longitude
        validated_data["end_latitude"] = end_city.latitude
        validated_data["end_longitude"] = end_city.longitude

        return super().create(validated_data)

    def validate(self, data):
        if data.get('departure_date') and data['departure_date'] < timezone.now().date():
            raise serializers.ValidationError("Departure date cannot be in the past.")

        if data.get('available_capacity') is not None:
            if isinstance(data['available_capacity'], str):
                data['available_capacity'] = float(data['available_capacity'])
            if data['available_capacity'] <= 0:
                raise serializers.ValidationError("Available capacity must be positive.")

        if data.get('max_weight') is not None:
            if isinstance(data['max_weight'], str):
                data['max_weight'] = float(''.join(filter(lambda c: c.isdigit() or c=='.', data['max_weight'])))
            if data['max_weight'] <= 0:
                raise serializers.ValidationError("Max weight must be positive.")

        return data
