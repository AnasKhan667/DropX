# route/models.py
from django.db import models
from delivery.models import Delivery
import uuid
from django.utils import timezone

class Route(models.Model):
    route_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='route')
    distance = models.FloatField(default=0.0)  # in km
    path = models.JSONField(null=True, blank=True)  # GeoJSON for route path
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Route for Delivery {self.delivery_id.delivery_id}"

    class Meta:
        indexes = [
            models.Index(fields=['delivery_id']),
        ]