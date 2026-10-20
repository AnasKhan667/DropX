# notification/urls.py
from django.urls import path
from .views import( NotificationListView,
                    NotificationDetailView, 
                    MarkNotificationAsReadView, 
                    MarkAllNotificationsAsReadView
                )
app_name = 'notification'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<uuid:notification_id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-read/<uuid:notification_id>/', MarkNotificationAsReadView.as_view(), name='mark-read'),
    path('mark-all-read/', MarkAllNotificationsAsReadView.as_view(), name='mark-all-read'),
]
