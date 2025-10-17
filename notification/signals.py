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
        def create_notification(user, notif_type, message):
            """
            Create notification only if it does not already exist.
            Prevents duplicate entries for the same event.
            """
            if user and not Notification.objects.filter(
                user_id=user,
                delivery_id=instance,
                type=notif_type
            ).exists():
                Notification.objects.create(
                    user_id=user,
                    delivery_id=instance,
                    type=notif_type,
                    message=message,
                    created_at=timezone.now()
                )

        # ✅ Driver fallback (if driver_id is null)
        driver_user = None
        if instance.driver_id:
            driver_user = instance.driver_id
        elif getattr(instance, "driver_post_id", None) and getattr(instance.driver_post_id, "user", None):
            driver_user = instance.driver_post_id.user

        # ------------------------------
        # Delivery created notifications
        # ------------------------------
        if created:
            create_notification(
                instance.sender_id,
                'Delivery Created',
                f'Delivery {instance.delivery_id} created.'
            )
            if instance.receiver_id:
                create_notification(
                    instance.receiver_id,
                    'Delivery Created',
                    f'You have a new delivery {instance.delivery_id} to receive.'
                )
            logger.info(f"Created notifications for delivery {instance.delivery_id}")

        # ------------------------------
        # Assigned status notifications
        # ------------------------------
        elif instance.status == DeliveryStatus.ASSIGNED:
            create_notification(
                instance.sender_id,
                'Delivery Accepted',
                f'Delivery {instance.delivery_id} accepted by driver {driver_user.email if driver_user else "unknown"}.'  
            )
            if instance.receiver_id:
                create_notification(
                    instance.receiver_id,
                    'Delivery Accepted',
                    f'Delivery {instance.delivery_id} has been accepted by a driver.'
                )
            logger.info(f"Created accepted notifications for delivery {instance.delivery_id}")

        # ------------------------------
        # In transit
        # ------------------------------
        elif instance.status == DeliveryStatus.IN_TRANSIT:
            create_notification(
                instance.sender_id,
                'Delivery In Transit',
                f'Delivery {instance.delivery_id} is in transit.'
            )
            if instance.receiver_id:
                create_notification(
                    instance.receiver_id,
                    'Delivery In Transit',
                    f'Delivery {instance.delivery_id} is on its way.'
                )
            logger.info(f"Created in-transit notifications for delivery {instance.delivery_id}")

        # ------------------------------
        # Delivered
        # ------------------------------
        elif instance.status == DeliveryStatus.DELIVERED:
            create_notification(
                instance.sender_id,
                'Delivery Completed',
                f'Delivery {instance.delivery_id} has been delivered.'
            )
            if instance.receiver_id:
                create_notification(
                    instance.receiver_id,
                    'Delivery Completed',
                    f'Delivery {instance.delivery_id} has been delivered to you.'
                )
            logger.info(f"Created delivered notifications for delivery {instance.delivery_id}")

        # ------------------------------
        # Cancelled
        # ------------------------------
        elif instance.status == DeliveryStatus.CANCELLED:
            create_notification(
                instance.sender_id,
                'Delivery Cancelled',
                f'Delivery {instance.delivery_id} has been cancelled.'
            )
            if instance.receiver_id:
                create_notification(
                    instance.receiver_id,
                    'Delivery Cancelled',
                    f'Delivery {instance.delivery_id} has been cancelled.'
                )
            logger.info(f"Created cancelled notifications for delivery {instance.delivery_id}")

    except Exception as e:
        logger.error(f"Error creating notifications for delivery {instance.delivery_id}: {str(e)}")
