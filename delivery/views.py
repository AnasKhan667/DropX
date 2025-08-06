from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Delivery, Package
from .serializers import DeliverySerializer, PackageSerializer
from route.models import Route
from notification.models import Notification
from django.utils import timezone

# Existing generic views
class DeliveryListCreateView(generics.ListCreateAPIView):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

class DeliveryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    lookup_field = 'delivery_id'

class PackageListCreateView(generics.ListCreateAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer

class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    lookup_field = 'package_id'

# Custom APIView for creating a delivery with cost calculation
class CreateDeliveryWithCostView(APIView):
    def post(self, request):
        serializer = DeliverySerializer(data=request.data)
        if serializer.is_valid():
            # Simulate cost calculation (e.g., based on package weight and distance)
            delivery = serializer.save()
            
            # Assume we have a related route for distance
            route = Route.objects.filter(delivery_id=delivery).first()
            distance = route.distance if route else 0
            
            # Calculate cost: $1 per km + $0.5 per kg of package weight
            packages = Package.objects.filter(delivery_id=delivery)
            total_weight = sum(package.weight for package in packages)
            delivery.total_cost = (distance * 1.0) + (total_weight * 0.5)
            delivery.save()
            
            # Trigger a notification to the receiver
            Notification.objects.create(
                user_id=delivery.receiver_id,
                delivery_id=delivery,
                type='Delivery Created',
                message=f'A new delivery has been created for you: {delivery.delivery_id}',
                is_read=False,
                created_at=timezone.now()
            )
            
            return Response(DeliverySerializer(delivery).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)