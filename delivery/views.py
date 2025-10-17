from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Delivery, DeliveryStatus, DeliveryLog, Package
from .serializers import DeliveryReadSerializer, DeliveryWriteSerializer
from notification.models import Notification

from django.utils import timezone
from route.models import Route
import requests
from DropX.permissions import IsSender, IsVerifiedDriver
import logging
from decimal import Decimal
from django.db import models

logger = logging.getLogger(__name__)


class DeliveryListCreateView(generics.ListCreateAPIView):
    queryset = Delivery.objects.all()
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DeliveryWriteSerializer
        return DeliveryReadSerializer

    def perform_create(self, serializer):
        serializer.save(sender_id=self.request.user)


class DeliveryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Delivery.objects.all()
    lookup_field = 'delivery_id'
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DeliveryWriteSerializer
        return DeliveryReadSerializer


class DeliveryAcceptView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.get(delivery_id=delivery_id, status=DeliveryStatus.PENDING)
        except Delivery.DoesNotExist:
            return Response({"error": "Delivery not found or not pending"}, status=status.HTTP_404_NOT_FOUND)

        if delivery.driver_post_id.user != request.user:
            return Response({"error": "You can only manage deliveries for your own posts."}, status=status.HTTP_403_FORBIDDEN)

        total_weight = sum(p.weight for p in delivery.packages.all())
        used_weight = sum(
            d.packages.aggregate(models.Sum('weight'))['weight__sum'] or 0
            for d in Delivery.objects.filter(
                driver_post_id=delivery.driver_post_id,
                status__in=[DeliveryStatus.ASSIGNED, DeliveryStatus.IN_TRANSIT]
            )
        )
        if total_weight + used_weight > delivery.driver_post_id.max_weight:
            return Response({"error": "Total package weight exceeds remaining capacity."}, status=status.HTTP_400_BAD_REQUEST)

        if delivery.pickup_address.get('city') != delivery.driver_post_id.start_city.name \
           or delivery.dropoff_address.get('city') != delivery.driver_post_id.end_city.name:
            return Response({"error": "Pickup and dropoff cities must match driver post route."}, status=status.HTTP_400_BAD_REQUEST)

        delivery.status = DeliveryStatus.ASSIGNED
        delivery.driver_id = request.user
        delivery.driver_post_id.status = 'Booked'
        delivery.driver_post_id.save()
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Accepted",
            comments=f"Delivery accepted by {request.user.email}"
        )
        return Response({"message": f"Delivery {delivery_id} accepted"}, status=status.HTTP_200_OK)


class DeliveryRejectView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.get(delivery_id=delivery_id, status=DeliveryStatus.PENDING)
        except Delivery.DoesNotExist:
            return Response({"error": "Delivery not found or not pending"}, status=status.HTTP_404_NOT_FOUND)

        if delivery.driver_post_id.user != request.user:
            return Response({"error": "You can only manage deliveries for your own posts."}, status=status.HTTP_403_FORBIDDEN)

        delivery.status = DeliveryStatus.REJECTED
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Rejected",
            comments=f"Delivery rejected by {request.user.email}"
        )
        return Response({"message": f"Delivery {delivery_id} rejected"}, status=status.HTTP_200_OK)


class CreateDeliveryWithCostView(generics.CreateAPIView):
    serializer_class = DeliveryWriteSerializer
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        delivery = serializer.save(sender_id=self.request.user)
        packages = Package.objects.filter(delivery_id=delivery)
        total_weight = sum(package.weight for package in packages)

        pickup = delivery.pickup_address
        dropoff = delivery.dropoff_address

        distance = 0
        path = None
        try:
            pickup_lon = float(pickup['longitude'])
            pickup_lat = float(pickup['latitude'])
            dropoff_lon = float(dropoff['longitude'])
            dropoff_lat = float(dropoff['latitude'])

            url = f"http://router.project-osrm.org/route/v1/driving/{pickup_lon},{pickup_lat};{dropoff_lon},{dropoff_lat}?overview=full&geometries=geojson"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('code') == 'Ok' and data.get('routes'):
                route_data = data['routes'][0]
                distance = route_data.get('distance', 0) / 1000
                geometry = route_data.get('geometry')
                if geometry and 'coordinates' in geometry and 'type' in geometry:
                    path = geometry
                    Route.objects.create(delivery_id=delivery, distance=distance, path=path)
        except Exception as e:
            logger.error(f"Route creation error for delivery {delivery.delivery_id}: {str(e)}")

        delivery.total_cost = (Decimal(str(distance)) * Decimal("1.0")) + (total_weight * Decimal("0.5"))
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Created",
            comments=f"Delivery created by {self.request.user.email}",
        )
