from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentDetailView,
    RefundPaymentView,
)

app_name = 'payment'

urlpatterns = [
    path('', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('payments/<uuid:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<uuid:payment_id>/refund/', RefundPaymentView.as_view(), name='payment-refund'),
]
