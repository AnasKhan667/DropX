from django.db import models
from accounts.models import CustomUser
from vehicle.models import Vehicle
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError

class City(models.Model):
    city_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100,null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=['name', 'country'])]

    def __str__(self):
        return self.name


class DriverPost(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Expired', 'Expired'),
        ('Booked', 'Booked'),
    ]

    post_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='driver_posts')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='driver_posts')
    start_city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='start_driver_posts')
    end_city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='end_driver_posts')
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    end_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    end_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    max_weight = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_city', 'end_city']),
            models.Index(fields=['departure_date']),
        ]

    def __str__(self):
        return f"Post {self.post_id} by {self.user.email}"

    def clean(self):
        if self.available_capacity <= 0 or self.max_weight <= 0:
            raise ValidationError("Capacity and weight must be positive.")
        if self.departure_date < timezone.now().date():
            raise ValidationError("Departure date cannot be in the past.")

        if (self.start_latitude is not None) != (self.start_longitude is not None):
            raise ValidationError("Both start latitude and longitude must be provided.")
        if (self.end_latitude is not None) != (self.end_longitude is not None):
            raise ValidationError("Both end latitude and longitude must be provided.")


class PostLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(DriverPost, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.log_id} for Post {self.post.post_id}"
