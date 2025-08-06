from django.db import models
from delivery.models import Delivery
import uuid

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('Wallet', 'Wallet'),
    ]
    PAYMENT_STATUSES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    REFUND_STATUSES = [
        ('None', 'None'),
        ('Requested', 'Requested'),
        ('Processed', 'Processed'),
        ('Denied', 'Denied'),
    ]

    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    failure_reason = models.CharField(max_length=255, null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUSES, default='None')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.payment_id} for Delivery {self.delivery_id}"