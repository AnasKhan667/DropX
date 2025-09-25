from django.urls import path
from .views import DriverPostListCreateView, DriverPostDetailView, MatchDriverPostView

app_name = 'driver_post'

urlpatterns = [
    path('', DriverPostListCreateView.as_view(), name='list-create'),
    path('<uuid:post_id>/', DriverPostDetailView.as_view(), name='detail'),
    path('match/<uuid:post_id>/', MatchDriverPostView.as_view(), name='match-post'),
]
