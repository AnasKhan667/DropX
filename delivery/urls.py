from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('', views.DeliveryListCreateView.as_view(), name='delivery-list-create'),
    path('create-with-cost/', views.CreateDeliveryWithCostView.as_view(), name='create-delivery-with-cost'),
    path('<uuid:delivery_id>/', views.DeliveryDetailView.as_view(), name='delivery-detail'),
    path('packages/', views.PackageListCreateView.as_view(), name='package-list-create'),
    path('packages/<uuid:package_id>/', views.PackageDetailView.as_view(), name='package-detail'),
]