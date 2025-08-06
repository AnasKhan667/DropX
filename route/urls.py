from django.urls import path
from .views import RouteListCreateView, RouteDetailView

app_name = 'route'

urlpatterns = [
    path('', RouteListCreateView.as_view(), name='route-list-create'),
    path('routes/<uuid:pk>/', RouteDetailView.as_view(), name='route-detail'),
]
