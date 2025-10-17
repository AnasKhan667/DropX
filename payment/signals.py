from django.db.models.signals import post_save
from django.dispatch import receiver
from delivery.models import Delivery, DeliveryLog
from .models import Payment
from notification.models import Notification
import logging
from django.utils import timezone
from chat.models import ChatRoom, Message

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Delivery)
def create_payment_on_delivery(sender, instance, created, **kwargs):
    logger.info(f"Delivery signal triggered: created={created}, delivery_id={instance.delivery_id}, total_cost={instance.total_cost}")
    try:
        if created and instance.total_cost > 0:
            payment = Payment.objects.create(
                delivery_id=instance,
                user_id=instance.sender_id,
                amount=instance.total_cost,
                payment_method='Cash',
                payment_status='Pending'
            )
            DeliveryLog.objects.create(
                delivery=instance,
                action="Payment Initiated",
                comments=f"Payment {payment.payment_id} created with method Cash"
            )
            Notification.objects.create(
                user_id=instance.sender_id,
                delivery_id=instance,
                type='Payment Initiated',
                message=f'Payment of {instance.total_cost} initiated for delivery {instance.delivery_id}.',
                created_at=timezone.now()
            )
            logger.info(f"Payment created for delivery {instance.delivery_id}")
    except Exception as e:
        logger.error(f"Error creating payment for delivery {instance.delivery_id}: {str(e)}")

@receiver(post_save, sender=Payment)
def notify_payment_update(sender, instance, created, **kwargs):
    try:
        message = ""
        log_action = ""
        if created and instance.payment_status == 'Pending':
            message = f'Payment of {instance.amount} is pending for delivery {instance.delivery_id.delivery_id}.'
            log_action = "Payment Pending"
            if instance.payment_method == 'Cash' and instance.delivery_id.driver_id:
                message += " Please negotiate in chat."
        elif instance.payment_status == 'Completed':
            message = f'Payment of {instance.amount} completed for delivery {instance.delivery_id.delivery_id}.'
            log_action = "Payment Completed"
            if instance.delivery_id.driver_id:
                Notification.objects.create(
                    user_id=instance.delivery_id.driver_id,
                    delivery_id=instance.delivery_id,
                    type='Payment Received',
                    message=f'Payment of {instance.amount} received for delivery {instance.delivery_id.delivery_id}.',
                    created_at=timezone.now()
                )
        elif instance.payment_status == 'Failed':
            message = f'Payment of {instance.amount} failed for delivery {instance.delivery_id.delivery_id}: {instance.failure_reason}.'
            log_action = "Payment Failed"
        elif instance.payment_status == 'Refunded':
            message = f'Payment of {instance.amount} refunded ({instance.refund_amount}) for delivery {instance.delivery_id.delivery_id}.'
            log_action = "Payment Refunded"
        if message:
            Notification.objects.create(
                user_id=instance.user_id,
                delivery_id=instance.delivery_id,
                type=log_action,
                message=message,
                created_at=timezone.now()
            )
            DeliveryLog.objects.create(
                delivery=instance.delivery_id,
                action=log_action,
                comments=message
            )
            logger.info(f"Notification and log created for payment {instance.payment_id}: {message}")
    except Exception as e:
        logger.error(f"Error creating notification/log for payment {instance.payment_id}: {str(e)}")


@receiver(post_save, sender=Delivery)
def create_payment_on_delivery(sender, instance, created, **kwargs):
    if created and instance.total_cost > 0:
        driver_phone = instance.driver_id.easypaisa_phone if instance.driver_id else None
        payment = Payment.objects.create(
            delivery_id=instance,
            user_id=instance.sender_id,
            amount=instance.total_cost,
            payment_method='EasyPaisa',  # Default to EasyPaisa per your idea
            payment_status='Pending',
            driver_easypaisa_phone=driver_phone
        )
        DeliveryLog.objects.create(
            delivery=instance,
            action="Payment Initiated",
            comments=f"Payment {payment.payment_id} pending. Sender: send to {driver_phone} via EasyPaisa."
        )
        Notification.objects.create(
            user_id=instance.sender_id,
            delivery_id=instance,
            type='Payment Initiated',
            message=f'Pay {instance.total_cost} to driver\'s EasyPaisa: {driver_phone}. Confirm in chat.'
        )


@receiver(post_save, sender=Payment)
def notify_payment_update(sender, instance, created, **kwargs):
    # ... existing code ...
    if instance.payment_status == 'Completed':
        # Trigger delivery acceptance
        instance.delivery_id.status = 'Accepted'  # Add status field to Delivery if not there
        instance.delivery_id.save()
        Notification.objects.create(
            user_id=instance.delivery_id.driver_id,
            delivery_id=instance.delivery_id,
            type='Delivery Accepted',
            message=f'Delivery {instance.delivery_id.delivery_id} accepted after payment confirmation.'
        )
