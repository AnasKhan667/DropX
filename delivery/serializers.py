from rest_framework import serializers
from .models import Delivery, Package
from accounts.models import CustomUser
from driver_post.models import DriverPost
from django.utils import timezone

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'package_id',
            'delivery_id',
            'description',
            'weight',
            'dimensions',
            'is_fragile',
            'created_at',
        ]
        read_only_fields = ['package_id', 'created_at']



class DeliverySerializer(serializers.ModelSerializer):
    packages = PackageSerializer(many=True, read_only=True)

    def validate_delivery_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value

    class Meta:
        model = Delivery
        fields = ['delivery_id', 'sender_id', 'receiver_id', 'driver_id', 'driver_post_id', 'pickup_address', 'dropoff_address', 'delivery_date', 'estimated_delivery_time', 'total_cost', 'status', 'created_at', 'updated_at', 'packages']
        read_only_fields = ['delivery_id', 'created_at', 'updated_at']

# class DeliverySerializer(serializers.ModelSerializer):
#     sender_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
#     receiver_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
#     driver_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False, allow_null=True)
#     driver_post_id = serializers.PrimaryKeyRelatedField(queryset=DriverPost.objects.all(), required=False, allow_null=True)

#     class Meta:
#         model = Delivery
#         fields = [
#             'delivery_id',
#             'sender_id',
#             'receiver_id',
#             'driver_id',
#             'driver_post_id',
#             'pickup_address',
#             'dropoff_address',
#             'delivery_date',
#             'estimated_delivery_time',
#             'total_cost',
#             'status',
#             'created_at',
#             'updated_at',
#         ]
#         read_only_fields = ['delivery_id', 'created_at', 'updated_at']
