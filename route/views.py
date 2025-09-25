from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Route
from .serializers import RouteSerializer
from delivery.models import Delivery, DeliveryStatus
from rest_framework import serializers
from driver_post.models import DriverPost
from DropX.permissions import IsSender, IsVerifiedDriver
import requests, json
import logging

logger = logging.getLogger(__name__)

class RouteListCreateView(generics.ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        delivery_id = serializer.validated_data['delivery_id_uuid']
        delivery = Delivery.objects.get(delivery_id=delivery_id)
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
                route = data['routes'][0]
                distance = route.get('distance', 0) / 1000
                geometry = route.get('geometry')
                if geometry and 'coordinates' in geometry and 'type' in geometry:
                    path = geometry
        except Exception as e:
            logger.error(f"Route creation error for delivery {delivery_id}: {str(e)}")

        serializer.save(delivery_id=delivery, distance=distance, path=path)


class RouteDetailView(generics.RetrieveUpdateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    lookup_field = 'route_id'
    permission_classes = [IsAuthenticated, IsSender | IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if user.role.lower() == 'sender':
            return Route.objects.filter(delivery_id__sender_id=user)
        return Route.objects.filter(delivery_id__driver_id=user)


class MultiDeliveryRouteView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedDriver]
    authentication_classes = [JWTAuthentication]

    def post(self, request, driver_post_id):
        try:
            # Get the DriverPost for the logged-in driver
            post = DriverPost.objects.get(post_id=driver_post_id, user=request.user)

            # Get deliveries assigned to this post
            deliveries = Delivery.objects.filter(
                driver_post_id=post,
                status__in=[DeliveryStatus.ASSIGNED, DeliveryStatus.IN_TRANSIT],
            )
            if not deliveries:
                return Response({"error": "No assigned deliveries for this post."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Build coordinates for OSRM
            coordinates = []
            for delivery in deliveries:
                pickup = delivery.pickup_address
                dropoff = delivery.dropoff_address
                coordinates.append(f"{float(pickup['longitude'])},{float(pickup['latitude'])}")
                coordinates.append(f"{float(dropoff['longitude'])},{float(dropoff['latitude'])}")

            coords_str = ";".join(coordinates)

            # OSRM API call
            url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
            response = requests.get(url, timeout=15)
            data = response.json()
            logger.debug(f"OSRM multi-delivery response: {data}")

            total_distance = 0
            path = None
            if data.get('code') == 'Ok' and data.get('routes'):
                route_data = data['routes'][0]
                total_distance = route_data.get('distance', 0) / 1000
                geometry = route_data.get('geometry')
                if geometry and isinstance(geometry, dict) and 'coordinates' in geometry:
                    path = geometry
                else:
                    logger.warning(f"Invalid geometry for multi-delivery post {driver_post_id}")
                    path = None
                    total_distance = 0

            # Save route for each delivery
            route_ids = []
            for delivery in deliveries:
                existing_route = Route.objects.filter(delivery_id=delivery).first()
                if existing_route:
                    existing_route.distance = total_distance
                    existing_route.path = path
                    existing_route.save()
                else:
                    route = Route.objects.create(
                        delivery_id=delivery,
                        distance=total_distance,
                        path=path
                    )
                    existing_route = route
                route_ids.append(str(existing_route.route_id))

            return Response({
                "post_id": str(post.post_id),
                "total_distance": total_distance,
                "path": path,
                "deliveries": [str(d.delivery_id) for d in deliveries],
                "routes_created": route_ids
            }, status=status.HTTP_200_OK)

        except DriverPost.DoesNotExist:
            logger.error(f"Driver post {driver_post_id} not found")
            return Response({"error": "Driver post not found."}, status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.RequestException as e:
            logger.error(f"OSRM request failed for post {driver_post_id}: {str(e)}")
            return Response({"error": "Unable to calculate route: OSRM request failed"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Multi-delivery route error for post {driver_post_id}: {str(e)}")
            return Response({"error": f"Unable to calculate multi-delivery route: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
