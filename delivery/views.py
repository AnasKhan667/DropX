from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import models
from django.utils import timezone
from decimal import Decimal
import requests
import logging

from .models import Delivery, DeliveryStatus, DeliveryLog, Package
from .serializers import DeliveryReadSerializer, DeliveryWriteSerializer
from notification.models import Notification
from route.models import Route
from DropX.permissions import IsSender, IsVerifiedDriver

logger = logging.getLogger(__name__)


class DeliveryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]
    serializer_class = DeliveryReadSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_cost', 'status']

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DeliveryWriteSerializer
        return DeliveryReadSerializer

    def get_queryset(self):
        return Delivery.objects.filter(sender_id=self.request.user)

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

        if not delivery.driver_post_id:
            return Response(
                {"error": "This delivery has no associated driver post."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if delivery.driver_post_id.user != request.user:
            return Response(
                {"error": "You can only manage deliveries for your own posts."},
                status=status.HTTP_403_FORBIDDEN
            )

        total_weight = sum(p.weight for p in delivery.packages.all())
        used_weight = sum(
            d.packages.aggregate(models.Sum('weight'))['weight__sum'] or 0
            for d in Delivery.objects.filter(
                driver_post_id=delivery.driver_post_id,
                status__in=[DeliveryStatus.ASSIGNED, DeliveryStatus.IN_TRANSIT]
            )
        )
        if total_weight + used_weight > delivery.driver_post_id.max_weight:
            return Response(
                {"error": "Total package weight exceeds remaining capacity."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if (
            delivery.pickup_address.get('city') != delivery.driver_post_id.start_city.name
            or delivery.dropoff_address.get('city') != delivery.driver_post_id.end_city.name
        ):
            return Response(
                {"error": "Pickup and dropoff cities must match driver post route."},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            return Response(
                {"error": "You can only manage deliveries for your own posts."},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery.status = DeliveryStatus.CANCELLED
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Rejected",
            comments=f"Delivery rejected by {request.user.email}"
        )
        return Response({"message": f"Delivery {delivery_id} rejected"}, status=status.HTTP_200_OK)


class DeliveryPickupView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.get(delivery_id=delivery_id, status=DeliveryStatus.ASSIGNED)
        except Delivery.DoesNotExist:
            return Response({"error": "Delivery not found or not assigned"}, status=status.HTTP_404_NOT_FOUND)

        if delivery.driver_id != request.user:
            return Response(
                {"error": "You can only manage your own deliveries."},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery.status = DeliveryStatus.IN_TRANSIT
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Picked Up",
            comments=f"Picked up by {request.user.email}"
        )
        return Response({"message": f"Delivery {delivery_id} is now in transit"}, status=status.HTTP_200_OK)


class DeliveryCompleteView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.get(delivery_id=delivery_id, status=DeliveryStatus.IN_TRANSIT)
        except Delivery.DoesNotExist:
            return Response({"error": "Delivery not in transit"}, status=status.HTTP_404_NOT_FOUND)

        if delivery.driver_id != request.user:
            return Response(
                {"error": "You can only complete your own deliveries."},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery.status = DeliveryStatus.DELIVERED
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Completed",
            comments=f"Delivered by {request.user.email}"
        )
        return Response({"message": f"Delivery {delivery_id} marked as delivered"}, status=status.HTTP_200_OK)


class DeliveryCancelView(APIView):
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]

    def post(self, request, delivery_id):
        try:
            delivery = Delivery.objects.get(delivery_id=delivery_id, sender_id=request.user)
        except Delivery.DoesNotExist:
            return Response({"error": "Delivery not found"}, status=status.HTTP_404_NOT_FOUND)

        if delivery.status not in [DeliveryStatus.PENDING, DeliveryStatus.ASSIGNED]:
            return Response(
                {"error": f"Cannot cancel delivery with status {delivery.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.status = DeliveryStatus.CANCELLED
        delivery.save()

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Cancelled",
            comments=f"Cancelled by {request.user.email}"
        )
        return Response({"message": f"Delivery {delivery_id} cancelled successfully"}, status=status.HTTP_200_OK)


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

            url = (
                f"http://router.project-osrm.org/route/v1/driving/"
                f"{pickup_lon},{pickup_lat};{dropoff_lon},{dropoff_lat}"
                f"?overview=full&geometries=geojson"
            )
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

        total_cost = (Decimal(str(distance)) * Decimal("1.0")) + (total_weight * Decimal("0.5"))

        # Use queryset.update() to avoid firing post_save a second time,
        # which would create a duplicate 'Delivery Created' notification.
        Delivery.objects.filter(pk=delivery.pk).update(total_cost=total_cost)

        DeliveryLog.objects.create(
            delivery=delivery,
            action="Delivery Created",
            comments=f"Delivery created by {self.request.user.email}",
        )


class DriverPendingDeliveryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]
    serializer_class = DeliveryReadSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'total_cost', 'status']

    def get_queryset(self):
        user = self.request.user
        driver_posts = user.driver_posts.all()
        return Delivery.objects.filter(
            driver_post_id__in=driver_posts
        ).order_by('-created_at')
