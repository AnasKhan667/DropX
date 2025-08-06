from django.db import models
from accounts.models import CustomUser
from delivery.models import Delivery
import uuid

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    reviewer_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_written')
    reviewed_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField()
    comment = models.TextField()
    review_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.review_id} by {self.reviewer_id.email}"