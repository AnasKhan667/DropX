from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Vehicle, VehicleLog
from .serializers import VehicleSerializer, VehicleLogSerializer
from DropX.permissions import IsVerifiedDriver
import logging

logger = logging.getLogger(__name__)


class VehicleListCreateView(generics.ListCreateAPIView):
    """
    Allows only verified drivers to list or create their vehicles.
    """
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]

    def get_queryset(self):
        # Only return vehicles belonging to the authenticated driver
        return Vehicle.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Save the vehicle with the authenticated user as owner
        vehicle = serializer.save(user=self.request.user, status='Active')
        VehicleLog.objects.create(
            vehicle=vehicle,
            action="Vehicle Created",
            comments=f"Vehicle {vehicle.number_plate} added by {self.request.user.email} (status: Active)"
        )
        logger.info(f"Vehicle {vehicle.vehicle_id} created by {self.request.user.email} (status: Active)")


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Allows only verified drivers to retrieve, update, or delete their own vehicles.
    """
    serializer_class = VehicleSerializer
    lookup_field = 'vehicle_id'
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]

    def get_queryset(self):
        # Only allow access to vehicles owned by the authenticated driver
        return Vehicle.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        vehicle = serializer.save()
        VehicleLog.objects.create(
            vehicle=vehicle,
            action="Vehicle Updated",
            comments=f"Vehicle {vehicle.number_plate} updated by {self.request.user.email}"
        )
        logger.info(f"Vehicle {vehicle.vehicle_id} updated by {self.request.user.email}")

    def perform_destroy(self, instance):
        VehicleLog.objects.create(
            vehicle=instance,
            action="Vehicle Deleted",
            comments=f"Vehicle {instance.number_plate} deleted by {instance.user.email}"
        )
        logger.info(f"Vehicle {instance.vehicle_id} deleted by {instance.user.email}")
        instance.delete()


class VehicleLogListView(generics.ListAPIView):
    """
    Allows only verified drivers to see logs of their own vehicles.
    """
    serializer_class = VehicleLogSerializer
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]
    parser_classes = [JSONParser]

    def get_queryset(self):
        # Only logs of the authenticated user's vehicles
        return VehicleLog.objects.filter(vehicle__user=self.request.user)
