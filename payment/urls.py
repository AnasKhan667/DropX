from django.urls import path
from .views import PaymentListView, PaymentCreateView, PaymentDetailView, RefundPaymentView

app_name = 'payment'

urlpatterns = [
    path('', PaymentListView.as_view(), name='list'),
    path('create/', PaymentCreateView.as_view(), name='create'),
    path('<uuid:payment_id>/', PaymentDetailView.as_view(), name='detail'),
    path('refund/<uuid:payment_id>/', RefundPaymentView.as_view(), name='refund'),

]