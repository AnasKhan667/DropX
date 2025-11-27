from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('', views.DeliveryListCreateView.as_view(), name='delivery-list-create'),
    path('<uuid:delivery_id>/', views.DeliveryDetailView.as_view(), name='delivery-detail'),
    path('<uuid:delivery_id>/accept/', views.DeliveryAcceptView.as_view(), name='delivery-accept'),
    path('<uuid:delivery_id>/reject/', views.DeliveryRejectView.as_view(), name='delivery-reject'),
    path('create-with-cost/', views.CreateDeliveryWithCostView.as_view(), name='create-with-cost'),
    path('driver/pending-deliveries/', views.DriverPendingDeliveryListView.as_view(), name='driver-pending-deliveries'),

    path('<uuid:delivery_id>/accept/', views.DeliveryAcceptView.as_view(), name='delivery-accept'),
    path('<uuid:delivery_id>/reject/', views.DeliveryRejectView.as_view(), name='delivery-reject'),
    path('<uuid:delivery_id>/pickup/', views.DeliveryPickupView.as_view(), name='delivery-pickup'),
    path('<uuid:delivery_id>/deliver/', views.DeliveryCompleteView.as_view(), name='delivery-deliver'),
    path('<uuid:delivery_id>/cancel/', views.DeliveryCancelView.as_view(), name='delivery-cancel'),  # ✅ Sender cancel

]
   