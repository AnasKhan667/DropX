from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import CustomUser
from apps.delivery.models import Delivery
import uuid

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    reviewer_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_written')
    reviewed_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    review_type = models.CharField(
        max_length=50,
        choices=[
            ('Sender to Driver', 'Sender to Driver'),
            ('Driver to Sender', 'Driver to Sender'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.review_id} By {self.reviewer_id.email}"