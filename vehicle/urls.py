from django.urls import path
from .views import (
    VehicleListCreateView,
    VehicleDetailView,
    VehicleLogListView
)

urlpatterns = [
    # Vehicles
    path('vehicles/', VehicleListCreateView.as_view(), name='vehicle-list-create'),
    path('vehicles/<uuid:vehicle_id>/', VehicleDetailView.as_view(), name='vehicle-detail'),

    # Vehicle Logs
    path('vehicle-logs/', VehicleLogListView.as_view(), name='vehicle-log-list'),
]
