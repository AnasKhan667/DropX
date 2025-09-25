from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Notification
from .serializers import NotificationSerializer
import logging
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

class NotificationListView(generics.ListAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Notification.objects.filter(user_id=self.request.user).order_by('-created_at')

class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Notification.objects.filter(user_id=self.request.user)

class MarkNotificationAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, notification_id):
        try:
            notification = get_object_or_404(Notification, notification_id=notification_id, user_id=request.user)
            notification.is_read = True
            notification.save()
            logger.info(f"Notification {notification_id} marked as read by {request.user.email}")
            return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return Response({'error': f"Failed to mark notification as read: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class MarkAllNotificationsAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            notifications = Notification.objects.filter(user_id=request.user, is_read=False)
            count = notifications.count()
            notifications.update(is_read=True)
            logger.info(f"{count} notifications marked as read for {request.user.email}")
            return Response({'message': f'{count} notifications marked as read.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error marking all notifications as read for {request.user.email}: {str(e)}")
            return Response({'error': f"Failed to mark notifications as read: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)