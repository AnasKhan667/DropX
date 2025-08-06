from django.urls import path
from .views import DriverVerificationListCreateView, VerificationLogListView

urlpatterns = [
    path('verifications/', DriverVerificationListCreateView.as_view(), name='driver-verification'),
    path('verification-logs/', VerificationLogListView.as_view(), name='verification-logs'),
]


# from django.urls import path
# from .views import DriverVerificationListCreateView, DriverVerificationDetailView, VerificationLogListView

# app_name = 'driver_verification'

# urlpatterns = [
#     path('', DriverVerificationListCreateView.as_view(), name='list-create'),
#     path('<uuid:verification_id>/', DriverVerificationDetailView.as_view(), name='detail'),
#     path('logs/', VerificationLogListView.as_view(), name='log-list'),
# ]
# from django.urls import path
# from .views import DriverVerificationListCreateView, DriverVerificationDetailView, VerificationLogListView, VerifyDriverView

# app_name = 'driver_verification'

# urlpatterns = [
#     path('', DriverVerificationListCreateView.as_view(), name='list-create'),
#     path('<uuid:verification_id>/', DriverVerificationDetailView.as_view(), name='detail'),
#     path('logs/', VerificationLogListView.as_view(), name='log-list'),
#     path('verify/<uuid:verification_id>/', VerifyDriverView.as_view(), name='verify'),
# ]
