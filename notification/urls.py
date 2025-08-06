from django.urls import path
from .views import (
    NotificationListCreateView,
    NotificationDetailView,
    MarkNotificationAsReadView,
    MarkAllNotificationsAsReadView
)

app_name = 'notification'

urlpatterns = [
    path('', NotificationListCreateView.as_view(), name='notification-list-create'),
    path('notifications/<uuid:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<uuid:notification_id>/read/', MarkNotificationAsReadView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read/', MarkAllNotificationsAsReadView.as_view(), name='notifications-mark-all-read'),
]
