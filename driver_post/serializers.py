from rest_framework import serializers
from .models import DriverPost, City, PostLog
from accounts.serializers import CustomUserSerializer
from vehicle.models import Vehicle
from django.utils import timezone


class CitySerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = City
        fields = ['city_id', 'name', 'state', 'country', 'latitude', 'longitude']
        extra_kwargs = {
            'name': {'validators': []},
        }


class PostLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLog
        fields = ['log_id', 'post', 'action', 'comments', 'timestamp']
        read_only_fields = ['log_id', 'timestamp']



class DriverPostSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    logs = PostLogSerializer(many=True, read_only=True)

    # write-only fields (input)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        source='vehicle',
        write_only=True,
        required=True
    )
    start_city_data = CitySerializer(write_only=True, required=True)
    end_city_data = CitySerializer(write_only=True, required=True)

    # read-only city names (output)
    start_city_name = serializers.SerializerMethodField(read_only=True)
    end_city_name = serializers.SerializerMethodField(read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.model', read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = DriverPost
        fields = [
            'post_id', 'user', 'logs', 'vehicle',
            'vehicle_name', 'vehicle_id',

            # write-only
            'start_city_data', 'end_city_data',

            # read-only
            'start_city_name', 'end_city_name',

            'departure_date', 'departure_time',
            'max_weight',
            'start_latitude', 'start_longitude',
            'end_latitude', 'end_longitude',
            'status',
        ]

        read_only_fields = [
            'post_id', 'logs', 'vehicle',
            'start_latitude', 'start_longitude',
            'end_latitude', 'end_longitude',
            'start_city_name', 'end_city_name',
            'status',
        ]

    # ------------- USER SERIALIZER -------------
    def get_user(self, obj):
        return CustomUserSerializer(obj.user).data if obj.user else None

    # ------------- CITY NAME FIELDS -------------
    def get_start_city_name(self, obj):
        return obj.start_city.name if obj.start_city else None

    def get_end_city_name(self, obj):
        return obj.end_city.name if obj.end_city else None

    # ------------- VALIDATIONS -------------
    def validate_vehicle_id(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError("Not your vehicle!")
        return value

    # ------------- CREATE -------------
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user

        start_city_data = validated_data.pop("start_city_data")
        end_city_data = validated_data.pop("end_city_data")

        start_city, _ = City.objects.get_or_create(
            name=start_city_data["name"],
            state=start_city_data.get("state") or "",
            country=start_city_data.get("country") or "",
            defaults={
                "latitude": start_city_data.get("latitude"),
                "longitude": start_city_data.get("longitude")
            },
        )

        end_city, _ = City.objects.get_or_create(
            name=end_city_data["name"],
            state=end_city_data.get("state") or "",
            country=end_city_data.get("country") or "",
            defaults={
                "latitude": end_city_data.get("latitude"),
                "longitude": end_city_data.get("longitude")
            },
        )

        validated_data["start_city"] = start_city
        validated_data["end_city"] = end_city
        validated_data["start_latitude"] = start_city.latitude
        validated_data["start_longitude"] = start_city.longitude
        validated_data["end_latitude"] = end_city.latitude
        validated_data["end_longitude"] = end_city.longitude

        return super().create(validated_data)

    # ------------- UPDATE -------------
    def update(self, instance, validated_data):
        vehicle = validated_data.get('vehicle', None)
        if vehicle and vehicle.user != self.context['request'].user:
            raise serializers.ValidationError("Ye vehicle aapka nahi hai!")
        return super().update(instance, validated_data)

    # ------------- VALIDATE FIELDS -------------
    def validate(self, data):
        if data.get('departure_date') and data['departure_date'] < timezone.now().date():
            raise serializers.ValidationError("Departure date cannot be in the past.")

        if data.get('max_weight') is not None:
            if isinstance(data['max_weight'], str):
                data['max_weight'] = float(''.join(c for c in data['max_weight'] if c.isdigit() or c == '.'))
            if data['max_weight'] <= 0:
                raise serializers.ValidationError("Max weight must be positive.")

        return data



class DriverPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverPost
        fields = ['departure_date', 'departure_time', 'max_weight']
