from django.db import models
from accounts.models import CustomUser
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('approved', 'approved'),
        ('pending', 'pending'),
    ]

    vehicle_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vehicles')

    # Vehicle type and description
    vehicle_type_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    # Vehicle details
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    number_plate = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.make} {self.model} ({self.number_plate}) by {self.user.email}"

    def clean(self):
        if self.year < 1900 or self.year > timezone.now().year + 1:
            raise ValidationError("Invalid vehicle year.")

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['number_plate']),
        ]


class VehicleLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    comments = models.TextField(blank=True)  # comments field retained
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.log_id} for Vehicle {self.vehicle.number_plate}"
