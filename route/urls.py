# route/urls.py
from django.urls import path
from .views import RouteListCreateView, RouteDetailView, MultiDeliveryRouteView

app_name = 'route'

urlpatterns = [
    path('', RouteListCreateView.as_view(), name='list-create'),
    path('<uuid:route_id>/', RouteDetailView.as_view(), name='detail'),
    path('multi-delivery/<uuid:driver_post_id>/', MultiDeliveryRouteView.as_view(), name='multi-delivery'),
]