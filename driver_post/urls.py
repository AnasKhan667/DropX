from django.urls import path
from .views import (
    DriverPostListCreateView,
    DriverPostDetailView,
    MatchDriverPostView,
    CityListCreateView,
    CityDetailView,
)

app_name = 'driver_post'

urlpatterns = [
    # DriverPost endpoints
    path('', DriverPostListCreateView.as_view(), name='driverpost-list-create'),
    path('driverposts/<uuid:pk>/', DriverPostDetailView.as_view(), name='driverpost-detail'),
    path('driverposts/<uuid:post_id>/match/', MatchDriverPostView.as_view(), name='match-driverpost'),

    # City endpoints
    path('cities/', CityListCreateView.as_view(), name='city-list-create'),
    path('cities/<int:pk>/', CityDetailView.as_view(), name='city-detail'),
]
