from django.db import models
from accounts.models import CustomUser
from delivery.models import Delivery
import uuid

class Chat(models.Model):
    chat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_chats')
    receiver_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_chats')
    delivery_id = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.chat_id} between {self.sender_id.email} and {self.receiver_id.email}"