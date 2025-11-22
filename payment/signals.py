from django.db.models.signals import post_save
from django.dispatch import receiver
from delivery.models import Delivery, DeliveryLog
from .models import Payment
from notification.models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# --- Create Payment when a new Delivery is created ---
@receiver(post_save, sender=Delivery)
def create_payment_on_delivery(sender, instance, created, **kwargs):
    if created and instance.total_cost > 0:
        driver_phone = instance.driver_id.easypaisa_phone if instance.driver_id else None
        payment_method = 'EasyPaisa' if driver_phone else 'Cash'
        payment = Payment.objects.create(
            delivery_id=instance,
            user_id=instance.sender_id,
            amount=instance.total_cost,
            payment_method=payment_method,
            payment_status='Pending',
            driver_easypaisa_phone=driver_phone
        )
        DeliveryLog.objects.create(
            delivery=instance,
            action="Payment Initiated",
            comments=f"Payment {payment.payment_id} pending. Method: {payment_method}."
        )
        Notification.objects.create(
            user_id=instance.sender_id,
            delivery_id=instance,
            type='Payment Initiated',
            message=f'Payment of {instance.total_cost} initiated. Please pay via {payment_method}.'
        )
        logger.info(f"Payment {payment.payment_id} created for delivery {instance.delivery_id}")

# --- Update Payment when Delivery status changes to InTransit ---
@receiver(post_save, sender=Delivery)
def update_payment_on_delivery_status(sender, instance, created, **kwargs):
    if not created and instance.status == 'InTransit':
        try:
            payment = Payment.objects.get(delivery_id=instance)
            if payment.payment_status == 'Pending':
                payment.payment_status = 'Completed'
                payment.save()

                DeliveryLog.objects.create(
                    delivery=instance,
                    action="Payment Completed",
                    comments=f"Payment {payment.payment_id} automatically completed because delivery is InTransit."
                )
                Notification.objects.create(
                    user_id=instance.sender_id,
                    delivery_id=instance,
                    type='Payment Completed',
                    message=f'Payment of {payment.amount} completed automatically as delivery {instance.delivery_id} is now InTransit.'
                )
                logger.info(f"Payment {payment.payment_id} updated to Completed due to delivery status InTransit")
        except Payment.DoesNotExist:
            logger.warning(f"No payment found for delivery {instance.delivery_id} to update.")

# --- Notify Payment updates ---
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
            # Trigger delivery acceptance
            instance.delivery_id.status = 'Accepted'
            instance.delivery_id.save()
            if instance.delivery_id.driver_id:
                Notification.objects.create(
                    user_id=instance.delivery_id.driver_id,
                    delivery_id=instance.delivery_id,
                    type='Delivery Accepted',
                    message=f'Delivery {instance.delivery_id.delivery_id} accepted after payment completion.'
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
