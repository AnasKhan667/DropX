from django.shortcuts import render
from .models import Vehicle, VehicleType
from .serializers import VehicleSerializer, VehicleTypeSerializer
from DropX.permissions import IsVerifiedDriver
from rest_framework import generics

# Create your views here.
class VehicleTypeListCreateView(generics.ListCreateAPIView):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer

class VehicleTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleSerializer
    lookup_field = 'vehicle_type_id'

class VehicleListCreateView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsVerifiedDriver]

class VehicleDatailViewDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    lookup_field = 'vehicle_id'
    permission_classes = [IsVerifiedDriver]