from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Payment
from .serializers import PaymentSerializer

# List all payments and allow creating new ones
class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

# Retrieve, update, or delete a specific payment
class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

# Refund a payment (custom logic - optional)
class RefundPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, payment_id=payment_id)

        refund_amount = request.data.get('refund_amount')
        if refund_amount is None:
            return Response({'error': 'refund_amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        if refund_amount > payment.amount:
            return Response({'error': 'Refund amount exceeds original payment'}, status=status.HTTP_400_BAD_REQUEST)

        payment.refund_amount = refund_amount
        payment.refund_status = "Refunded"
        payment.save()

        return Response({'message': 'Payment refunded successfully'}, status=status.HTTP_200_OK)
