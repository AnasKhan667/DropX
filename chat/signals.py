from django.db.models.signals import post_save
from django.dispatch import receiver
from payment.models import Payment
from .models import ChatRoom, Message
from notification.models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Payment)
def create_chat_room_on_payment(sender, instance, created, **kwargs):
    if created and instance.payment_status == 'Pending':
        try:
            # ✅ Chat room create / get
            chat_room, room_created = ChatRoom.objects.get_or_create(delivery=instance.delivery_id)
            if room_created:
                logger.info(f"ChatRoom {chat_room.chat_room_id} created for payment {instance.payment_id}")

            # ✅ Determine receiver (driver)
            receiver_user = None
            if instance.delivery_id.driver_post_id:
                receiver_user = instance.delivery_id.driver_post_id.user  # Driver user

            # ✅ Initial message text
            initial_content = f"{instance.payment_method} payment of {instance.amount} pending for delivery {instance.delivery_id.delivery_id}. "
            if instance.payment_method == 'Cash':
                initial_content += "Please discuss terms."
            elif instance.payment_method == 'EasyPaisa':
                initial_content += f"Sender: Send to {instance.driver_easypaisa_phone}. Confirm here."

            # ✅ Create message
            Message.objects.create(
                chat_room=chat_room,
                sender=instance.user_id,
                receiver=instance.delivery_id.driver_post_id.user if instance.delivery_id.driver_post_id and instance.delivery_id.driver_post_id.user else None,
                content=initial_content,
                created_at=timezone.now()
            )

            # ✅ Create notification
            Notification.objects.create(
                user_id=receiver_user,
                delivery_id=instance.delivery_id,
                type=f'{instance.payment_method} Payment Pending',
                message=f'Sender initiated {instance.payment_method} payment for delivery {instance.delivery_id.delivery_id}. Chat to confirm.',
                created_at=timezone.now()
            )

            logger.info(f"Initial message and notification created for payment {instance.payment_id}")

        except Exception as e:
            logger.error(f"Error creating chat room for payment {instance.payment_id}: {str(e)}")
