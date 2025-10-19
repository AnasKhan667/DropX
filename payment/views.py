from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .models import Payment
from .serializers import PaymentSerializer
from DropX.permissions import IsSender, IsVerifiedDriver
from delivery.models import Delivery, DeliveryLog
import logging
import uuid
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class PaymentListView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        role = (user.role or "").lower()  # ✅ lowercase for safety
        if role == 'sender':
            return Payment.objects.filter(user_id=user)
        elif role == 'driver':
            return Payment.objects.filter(delivery_id__driver_id=user)
        return Payment.objects.none()


class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        delivery = get_object_or_404(Delivery, delivery_id=serializer.validated_data['delivery_id_id'])
        user = self.request.user  # Sender
        payment_method = serializer.validated_data['payment_method']
        amount = delivery.total_cost
        sender_notes = serializer.validated_data.get('sender_notes')
        cod_notes = serializer.validated_data.get('cod_notes')

        # Pull driver's EasyPaisa phone if method is EasyPaisa
        driver_easypaisa_phone = None
        if payment_method == 'EasyPaisa':
            if not delivery.driver_id or not delivery.driver_id.easypaisa_phone:
                raise ValidationError("Driver has no EasyPaisa phone registered.")
            driver_easypaisa_phone = delivery.driver_id.easypaisa_phone

        try:
            payment = serializer.save(
                delivery_id=delivery,
                user_id=user,
                payment_status='Pending',
                transaction_id=str(uuid.uuid4())[:8] if payment_method == 'EasyPaisa' else None,
                sender_notes=sender_notes,
                cod_notes=cod_notes if payment_method == 'Cash' else None,
                driver_easypaisa_phone=driver_easypaisa_phone
            )

            DeliveryLog.objects.create(
                delivery=delivery,
                action="Payment Pending",
                comments=f"Payment {payment.payment_id} created with method {payment_method}. Use chat to confirm."
            )
            logger.info(f"Payment {payment.payment_id} created for delivery {delivery.delivery_id}")
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'payment_id'

    def get_queryset(self):
        user = self.request.user
        role = (user.role or "").lower()  # ✅ lowercase for safety
        if role == 'sender':
            return Payment.objects.filter(user_id=user)
        elif role == 'driver':
            return Payment.objects.filter(delivery_id__driver_id=user)
        return Payment.objects.none()

    def perform_update(self, serializer):
        # Allow driver to update status to Completed after manual verification
        instance = serializer.instance
        if self.request.user.role.lower() == 'driver' and 'payment_status' in serializer.validated_data:
            new_status = serializer.validated_data['payment_status']
            if new_status == 'Completed' and instance.payment_status == 'Pending':
                serializer.save()
                DeliveryLog.objects.create(
                    delivery=instance.delivery_id,
                    action="Payment Completed",
                    comments="Driver confirmed manual payment."
                )
                # Optionally trigger delivery acceptance here
                instance.delivery_id.status = 'Accepted'  # Assume Delivery has a status field; add if not
                instance.delivery_id.save()


class RefundPaymentView(APIView):
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, payment_id=payment_id, user_id=request.user)
        refund_amount = request.data.get('refund_amount')

        if refund_amount is None or refund_amount > payment.amount or payment.payment_status != 'Completed':
            return Response({'error': 'Invalid refund request'}, status=status.HTTP_400_BAD_REQUEST)

        payment.refund_status = 'Processed'
        payment.refund_amount = refund_amount
        payment.payment_status = 'Refunded'
        payment.save()
        DeliveryLog.objects.create(
            delivery=payment.delivery_id,
            action="Payment Refunded",
            comments=f"Manual refund {refund_amount} processed."
        )
        return Response({'message': 'Refund processed (manual)'}, status=status.HTTP_200_OK)
