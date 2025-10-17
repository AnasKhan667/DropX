from rest_framework import serializers
from .models import Payment
from delivery.models import Delivery


class PaymentSerializer(serializers.ModelSerializer):
    delivery_id_id = serializers.UUIDField(write_only=True)
    delivery_id = serializers.UUIDField(source='delivery_id.delivery_id', read_only=True)
    user_id = serializers.UUIDField(source='user_id.id', read_only=True)

    driver_phone = serializers.CharField(source='delivery_id.driver_id.phone_number', read_only=True)

    sender_notes = serializers.CharField(write_only=True, required=False, allow_blank=True)
    cod_notes = serializers.CharField(write_only=True, required=False, allow_blank=True)

    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    refund_status_display = serializers.CharField(source='get_refund_status_display', read_only=True)

    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'payment_id', 'delivery_id', 'user_id', 'delivery_id_id',
            'amount', 'payment_method', 'payment_method_display',
            'payment_status', 'payment_status_display',
            'transaction_id', 'failure_reason', 'retry_count',
            'refund_status', 'refund_status_display', 'refund_amount',
            'created_at', 'updated_at', 'sender_notes', 'cod_notes',
            'driver_easypaisa_phone', 'driver_phone'
        ]
        read_only_fields = [
            'payment_id', 'transaction_id', 'failure_reason', 'retry_count',
            'created_at', 'updated_at', 'payment_status', 'refund_status',
            'delivery_id', 'user_id', 'driver_phone', 'driver_easypaisa_phone'
        ]

    def validate(self, data):
        delivery = Delivery.objects.filter(delivery_id=data.get('delivery_id_id')).first()
        if not delivery:
            raise serializers.ValidationError("Invalid delivery_id.")
        data['amount'] = delivery.total_cost
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user_id'] = request.user

        delivery = Delivery.objects.get(delivery_id=validated_data['delivery_id_id'])
        validated_data['amount'] = delivery.total_cost

        return super().create(validated_data)
