from django.db import models
from accounts.models import CustomUser
import uuid

class VehicleType(models.Model):
    vehicle_type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_name = models.CharField(max_length=50)
    max_capacity = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type_name

class Vehicle(models.Model):
    vehicle_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type_id = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    license_plate = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=30)
    insurance = models.JSONField()
    registration_document = models.FileField(upload_to='registrations/')
    capacity = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.make} {self.model} ({self.license_plate})"