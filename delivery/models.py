from django.db import models
from accounts.models import CustomUser
from driver_post.models import DriverPost, City
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError


class DeliveryStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    ASSIGNED = 'Assigned', 'Assigned'
    IN_TRANSIT = 'In Transit', 'In Transit'
    DELIVERED = 'Delivered', 'Delivered'
    CANCELLED = 'Cancelled', 'Cancelled'


class Delivery(models.Model):
    delivery_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_deliveries')
    receiver_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_deliveries', null=True, blank=True)
    driver_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driven_deliveries', null=True, blank=True)
    driver_post_id = models.ForeignKey(DriverPost, on_delete=models.CASCADE, null=True, blank=True)
    pickup_address = models.JSONField()
    dropoff_address = models.JSONField()
    pickup_city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='pickup_deliveries')
    dropoff_city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='dropoff_deliveries')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery created For {self.pickup_city} To {self.dropoff_city} From {self.sender_id.email}"

    def clean(self):
        if self.delivery_date < timezone.now().date():
            raise ValidationError("Delivery date must be in the future.")
        if self.driver_post_id:
            total_weight = sum(p.weight for p in self.packages.all())
            if total_weight > self.driver_post_id.max_weight:
                raise ValidationError("Total package weight exceeds driver post max weight.")
            if self.pickup_address.get('city') != self.driver_post_id.start_city.name or \
               self.dropoff_address.get('city') != self.driver_post_id.end_city.name:
                raise ValidationError("Pickup and dropoff cities must match driver post route.")

    def check_route_compatibility(self):
        if self.driver_post_id:
            return (
                self.pickup_address.get('city') == self.driver_post_id.start_city.name and
                self.dropoff_address.get('city') == self.driver_post_id.end_city.name
            )
        return False

    def get_remaining_capacity(self):
        if self.driver_post_id:
            used_weight = sum(
                d.packages.aggregate(models.Sum('weight'))['weight__sum'] or 0
                for d in Delivery.objects.filter(
                    driver_post_id=self.driver_post_id,
                    status__in=['Assigned', 'In Transit']
                )
            )
            return self.driver_post_id.max_weight - used_weight
        return 0


class Package(models.Model):
    package_id  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='packages')
    description = models.CharField(max_length=255)
    weight      = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    dimensions  = models.JSONField()  # {"length": 30, "width": 20, "height": 10}
    is_fragile  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Package {self.package_id} for Delivery {self.delivery_id}"


class DeliveryLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=255)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} - {self.delivery.delivery_id}"
