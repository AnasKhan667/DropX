from django.db import models
import uuid
from django.core.exceptions import ValidationError
from delivery.models import Delivery, DeliveryLog
from accounts.models import CustomUser


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash on Delivery'),
        ('EasyPaisa', 'EasyPaisa'),
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
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')  # Sender
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default='Pending')
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    failure_reason = models.CharField(max_length=255, null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUSES, default='None')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sender_notes = models.TextField(null=True, blank=True, help_text="Notes from sender, e.g., transaction ref")
    cod_notes = models.TextField(null=True, blank=True, help_text="Notes for COD")
    driver_easypaisa_phone = models.CharField(max_length=15, null=True, blank=True)  # Copied from driver on creation

    def __str__(self):
        return f"Payment Of {self.amount} For Delivery {self.delivery_id.pickup_city} To {self.delivery_id.dropoff_city}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be positive.")
        if self.payment_method == 'Cash' and self.delivery_id.driver_id is None:
            raise ValidationError("Driver must be assigned for Cash payments.")
        if self.refund_amount and self.refund_amount > self.amount:
            raise ValidationError("Refund amount cannot exceed payment amount.")
        if self.amount != self.delivery_id.total_cost:
            raise ValidationError("Payment amount must match delivery total_cost.")

    def save(self, *args, **kwargs):
        if self.payment_method == "EasyPaisa" and not self.driver_easypaisa_phone:
            # 1️⃣ Driver already assigned → usi ka number le lo
            if self.delivery_id and self.delivery_id.driver_id:
                driver = self.delivery_id.driver_id
                if hasattr(driver, "driver_profile") and driver.driver_profile.easypaisa_phone:
                    self.driver_easypaisa_phone = driver.driver_profile.easypaisa_phone
                elif hasattr(driver, "phone_number") and driver.phone_number:
                    self.driver_easypaisa_phone = driver.phone_number
            else:
                # 2️⃣ Driver abhi assign nahi hua → koi available driver ka EasyPaisa number pick karo
                from accounts.models import DriverProfile
                random_driver = DriverProfile.objects.filter(easypaisa_phone__isnull=False).first()
                if random_driver:
                    self.driver_easypaisa_phone = random_driver.easypaisa_phone

        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=['delivery_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment_status']),
        ]
