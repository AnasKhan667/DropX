from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import DriverPost, City, PostLog
from .serializers import DriverPostSerializer, CitySerializer, PostLogSerializer
from DropX.permissions import IsVerifiedDriver, IsDriver, IsSender
import logging
from django.utils import timezone

# DriverPost List/Create with permission
class DriverPostListCreateView(generics.ListCreateAPIView):
    queryset = DriverPost.objects.all()
    serializer_class = DriverPostSerializer
    permission_classes = [IsVerifiedDriver]

# DriverPost Retrieve/Update/Delete with permission
class DriverPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DriverPost.objects.all()
    serializer_class = DriverPostSerializer
    permission_classes = [IsVerifiedDriver]

# City List/Create (no custom permissions applied here, adjust as needed)
class CityListCreateView(generics.ListCreateAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

# City Retrieve/Update/Delete
class CityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

# Your existing MatchDriverPostView unchanged
class MatchDriverPostView(APIView):
    def post(self, request, post_id):
        try:
            post = DriverPost.objects.get(post_id=post_id)
        except DriverPost.DoesNotExist:
            return Response({'error': 'Driver post not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'message': f'Matched post {post_id} with a delivery'}, status=status.HTTP_200_OK)
