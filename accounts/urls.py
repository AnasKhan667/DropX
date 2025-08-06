from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<uuid:id>/', views.UserDetailView.as_view(), name='user-detail'),  # Changed to UUID
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    path('driver-register/', views.DriverRegisterView.as_view(), name='driver-register'),
    path('sender-register/', views.SenderRegisterView.as_view(), name='sender-register'),
    path('driver-login/', views.DriverLoginView.as_view(), name='driver-login'),
    path('sender-login/', views.SenderLoginView.as_view(), name='sender-login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]