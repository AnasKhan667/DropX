from rest_framework import serializers
from .models import Delivery, Package, DeliveryLog
from accounts.models import CustomUser
from accounts.serializers import CustomUserSerializer
from driver_post.serializers import DriverPostSerializer, CitySerializer
from decimal import Decimal
from route.models import Route
from route.serializers import RouteSerializer
from django.utils import timezone


class DimensionsSerializer(serializers.Serializer):
    length = serializers.FloatField()
    width = serializers.FloatField()
    height = serializers.FloatField()


class PackageSerializer(serializers.ModelSerializer):
    dimensions = DimensionsSerializer()
    weight = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Package
        fields = ['package_id', 'description', 'weight', 'dimensions', 'is_fragile', 'created_at']
        read_only_fields = ['package_id', 'created_at']


class DeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLog
        fields = ['log_id', 'delivery', 'action', 'comments', 'created_at']
        read_only_fields = ['log_id', 'created_at']


class AddressSerializer(serializers.Serializer):
    address_line = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField(allow_blank=True)
    country = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class DeliveryWriteSerializer(serializers.ModelSerializer):
    pickup_address = AddressSerializer()
    dropoff_address = AddressSerializer()
    packages = PackageSerializer(many=True, write_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Delivery
        fields = [
            'delivery_id', 'sender_id', 'driver_id', 'driver_post_id',
            'pickup_address', 'dropoff_address', 'delivery_date',
            'estimated_delivery_time', 'total_cost', 'status', 'packages',
        ]
        read_only_fields = ['delivery_id', 'sender_id', 'driver_id', ]

    def create(self, validated_data):
        pickup_data = validated_data.pop('pickup_address')
        dropoff_data = validated_data.pop('dropoff_address')
        packages_data = validated_data.pop('packages', [])
        driver_post = validated_data.get('driver_post_id')

        if driver_post:
            validated_data['pickup_city'] = driver_post.start_city
            validated_data['dropoff_city'] = driver_post.end_city

        validated_data['pickup_address'] = pickup_data
        validated_data['dropoff_address'] = dropoff_data

        delivery = super().create(validated_data)

        # calculate total_cost
        total_weight = sum(Decimal(p['weight']) for p in packages_data)
        delivery.total_cost = total_weight * Decimal("0.5")  # example calculation
        delivery.save()
        return delivery

    def validate_delivery_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value


class DeliveryReadSerializer(serializers.ModelSerializer):
    sender_id = CustomUserSerializer(read_only=True)
    driver_id = CustomUserSerializer(read_only=True)
    driver_post_id = DriverPostSerializer(read_only=True)
    packages = PackageSerializer(many=True, read_only=True)
    pickup_city = CitySerializer(read_only=True)
    dropoff_city = CitySerializer(read_only=True)
    pickup_address = AddressSerializer(read_only=True)
    dropoff_address = AddressSerializer(read_only=True)
    route = serializers.SerializerMethodField()
    logs = DeliveryLogSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Delivery
        fields = [
            'delivery_id', 'sender_id', 'driver_id', 'driver_post_id',
            'pickup_address', 'dropoff_address',
            'pickup_city', 'dropoff_city',
            'delivery_date', 'estimated_delivery_time', 'total_cost', 'status',
            'created_at', 'updated_at', 'packages', 'logs', 'route', 
        ]
        read_only_fields = [
            'delivery_id', 'sender_id', 'driver_id', 'created_at',
            'updated_at', 'logs', 'route', 
        ]

    def get_route(self, obj):
        route = Route.objects.filter(delivery_id=obj).first()
        return RouteSerializer(route).data if route else None

