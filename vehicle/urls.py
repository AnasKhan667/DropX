from django.urls import path
from .views import (
    VehicleTypeListCreateView,
    VehicleTypeDetailView,
    VehicleListCreateView,
    VehicleDatailViewDetail,
)

app_name = 'vehicle'

urlpatterns = [
    # Vehicle Types
    path('vehicle-types/', VehicleTypeListCreateView.as_view(), name='vehicle-type-list-create'),
    path('vehicle-types/<uuid:vehicle_type_id>/', VehicleTypeDetailView.as_view(), name='vehicle-type-detail'),

    # Vehicles
    path('vehicles/', VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path('vehicles/<uuid:vehicle_id>/', VehicleDatailViewDetail.as_view(), name='vehicle-detail'),
]
