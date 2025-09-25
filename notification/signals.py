from django.db.models.signals import post_save
from django.dispatch import receiver
from delivery.models import Delivery, DeliveryStatus
from .models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Delivery)
def notify_delivery_update(sender, instance, created, **kwargs):
    try:
        if created:
            # Notify sender
            Notification.objects.create(
                user_id=instance.sender_id,
                delivery_id=instance,
                type='Delivery Created',
                message=f'Delivery {instance.delivery_id} created.',
                created_at=timezone.now()
            )
            # Notify receiver if exists
            if instance.receiver_id:
                Notification.objects.create(
                    user_id=instance.receiver_id,
                    delivery_id=instance,
                    type='Delivery Created',
                    message=f'You have a new delivery {instance.delivery_id} to receive.',
                    created_at=timezone.now()
                )
            logger.info(f"Created notifications for delivery {instance.delivery_id}")
        elif instance.status == DeliveryStatus.ASSIGNED:
            Notification.objects.create(
                user_id=instance.sender_id,
                delivery_id=instance,
                type='Delivery Accepted',
                message=f'Delivery {instance.delivery_id} accepted by driver {instance.driver_id.email if instance.driver_id else "unknown"}.',
                created_at=timezone.now()
            )
            if instance.receiver_id:
                Notification.objects.create(
                    user_id=instance.receiver_id,
                    delivery_id=instance,
                    type='Delivery Accepted',
                    message=f'Delivery {instance.delivery_id} has been accepted by a driver.',
                    created_at=timezone.now()
                )
            logger.info(f"Created accepted notifications for delivery {instance.delivery_id}")
        elif instance.status == DeliveryStatus.IN_TRANSIT:
            Notification.objects.create(
                user_id=instance.sender_id,
                delivery_id=instance,
                type='Delivery In Transit',
                message=f'Delivery {instance.delivery_id} is in transit.',
                created_at=timezone.now()
            )
            if instance.receiver_id:
                Notification.objects.create(
                    user_id=instance.receiver_id,
                    delivery_id=instance,
                    type='Delivery In Transit',
                    message=f'Delivery {instance.delivery_id} is on its way.',
                    created_at=timezone.now()
                )
            logger.info(f"Created in-transit notifications for delivery {instance.delivery_id}")
        elif instance.status == DeliveryStatus.DELIVERED:
            Notification.objects.create(
                user_id=instance.sender_id,
                delivery_id=instance,
                type='Delivery Completed',
                message=f'Delivery {instance.delivery_id} has been delivered.',
                created_at=timezone.now()
            )
            if instance.receiver_id:
                Notification.objects.create(
                    user_id=instance.receiver_id,
                    delivery_id=instance,
                    type='Delivery Completed',
                    message=f'Delivery {instance.delivery_id} has been delivered to you.',
                    created_at=timezone.now()
                )
            logger.info(f"Created delivered notifications for delivery {instance.delivery_id}")
        elif instance.status == DeliveryStatus.CANCELLED:
            Notification.objects.create(
                user_id=instance.sender_id,
                delivery_id=instance,
                type='Delivery Cancelled',
                message=f'Delivery {instance.delivery_id} has been cancelled.',
                created_at=timezone.now()
            )
            if instance.receiver_id:
                Notification.objects.create(
                    user_id=instance.receiver_id,
                    delivery_id=instance,
                    type='Delivery Cancelled',
                    message=f'Delivery {instance.delivery_id} has been cancelled.',
                    created_at=timezone.now()
                )
            logger.info(f"Created cancelled notifications for delivery {instance.delivery_id}")
    except Exception as e:
        logger.error(f"Error creating notifications for delivery {instance.delivery_id}: {str(e)}")