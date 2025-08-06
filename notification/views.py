from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from django.shortcuts import get_object_or_404

# List all notifications for authenticated user and allow creation
class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user_id=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)

# Retrieve, update, or delete a single notification
class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user_id=self.request.user)

# Mark a notification as read
class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, notification_id=notification_id, user_id=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)

# Mark all notifications as read
class MarkAllNotificationsAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notifications = Notification.objects.filter(user_id=request.user, is_read=False)
        notifications.update(is_read=True)
        return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)
