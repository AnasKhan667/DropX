from django.db import models
from delivery.models import Delivery
import uuid

class Route(models.Model):
    route_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='routes')
    start_location = models.JSONField()
    end_location = models.JSONField()
    waypoints = models.JSONField()
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_time = models.IntegerField()
    actual_time = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Route {self.route_id} for Delivery {self.delivery_id}"