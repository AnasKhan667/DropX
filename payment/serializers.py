from rest_framework import serializers
from .models import Payment
from delivery.models import Delivery

class PaymentSerializer(serializers.ModelSerializer):
    delivery_id = serializers.PrimaryKeyRelatedField(queryset=Delivery.objects.all())

    class Meta:
        model = Payment
        fields = [
            'payment_id',
            'delivery_id',
            'amount',
            'payment_method',
            'payment_status',
            'transaction_id',
            'failure_reason',
            'retry_count',
            'refund_status',
            'refund_amount',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['payment_id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate(self, data):
        if data.get('refund_amount') and data['refund_amount'] > data['amount']:
            raise serializers.ValidationError("Refund amount cannot exceed payment amount.")
        return data

