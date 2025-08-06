from django.db import models
from accounts.models import CustomUser
from driver_post.models import DriverPost
import uuid

class DeliveryStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    ASSIGNED = 'Assigned', 'Assigned'
    IN_TRANSIT = 'In Transit', 'In Transit'
    DELIVERED = 'Delivered', 'Delivered'
    CANCELLED = 'Cancelled', 'Cancelled'

class Delivery(models.Model):
    delivery_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_deliveries')
    receiver_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_deliveries')
    driver_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driven_deliveries', null=True, blank=True)
    driver_post_id = models.ForeignKey(DriverPost, on_delete=models.CASCADE, null=True, blank=True)
    pickup_address = models.JSONField()
    dropoff_address = models.JSONField()
    delivery_date = models.DateField()
    estimated_delivery_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery {self.delivery_id} from {self.sender_id.email}"

class Package(models.Model):
    package_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='packages')
    description = models.CharField(max_length=255)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    dimensions = models.JSONField()
    is_fragile = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Package {self.package_id} for Delivery {self.delivery_id}"