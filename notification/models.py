from django.db import models
from accounts.models import CustomUser
from delivery.models import Delivery
import uuid

class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    type = models.CharField(max_length=50)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.notification_id} for {self.user_id.email}"