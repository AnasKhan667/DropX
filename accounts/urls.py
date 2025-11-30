from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<uuid:id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    
    # Driver endpoints
    path('driver-register/', views.DriverRegisterView.as_view(), name='driver-register'),
    path('driver-login/', views.DriverLoginView.as_view(), name='driver-login'),
    path('driver-logout/', views.DriverLogoutView.as_view(), name='driver-logout'),
    
    # Sender endpoints
    path('sender-register/', views.SenderRegisterView.as_view(), name='sender-register'),
    path('sender-login/', views.SenderLoginView.as_view(), name='sender-login'),
    path('sender-logout/', views.SenderLogoutView.as_view(), name='sender-logout'),
    
    # Generic logout (works for any role)
    path('logout/', views.LogoutView.as_view(), name='logout'),
]