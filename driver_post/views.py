from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import DriverPost, City, PostLog
from .serializers import DriverPostSerializer, CitySerializer, PostLogSerializer
from accounts.models import DriverProfile
from DropX.permissions import IsDriver, IsVerifiedDriver, IsSender
import logging
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

logger = logging.getLogger(__name__)


def get_or_create_city(city_data):
    city, _ = City.objects.get_or_create(
        name=city_data.get("name"),
        state=city_data.get("state"),
        country=city_data.get("country"),
        defaults={
            "latitude": city_data.get("latitude"),
            "longitude": city_data.get("longitude"),
        },
    )
    return city


class DriverPostListCreateView(generics.ListCreateAPIView):
    queryset = DriverPost.objects.all()
    serializer_class = DriverPostSerializer
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['start_city__name', 'end_city__name', 'departure_date', 'status']

    def get_permissions(self):
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated, IsVerifiedDriver]
        else:
            permission_classes = [IsAuthenticated, IsDriver | IsSender]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.user.role == 'driver':
            return DriverPost.objects.filter(user=self.request.user)
        return DriverPost.objects.filter(status__in=['Active', 'Booked'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return nested data including user & logs
        return Response(DriverPostSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        try:
            driver_profile = self.request.user.driver_profile
            if not driver_profile.is_driver_verified:
                raise PermissionDenied("Only verified drivers can create posts.")
            if not self.request.user.vehicles.filter(status='approved').exists():
                raise ValidationError("You must have an approved vehicle to create a post.")

            serializer.save(user=self.request.user)

            # Create log
            PostLog.objects.create(
                post=serializer.instance,
                action="Post Created",
                comments=f"Post created by {self.request.user.email} from {serializer.instance.start_city} to {serializer.instance.end_city}"
            )

        except DriverProfile.DoesNotExist:
            raise ValidationError("Driver profile not found.")


class DriverPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DriverPost.objects.all()
    serializer_class = DriverPostSerializer
    lookup_field = 'post_id'
    permission_classes = [IsAuthenticated, IsDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return DriverPost.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save()
        # Expire post if past date
        if instance.departure_date < timezone.now().date():
            instance.status = 'Expired'
            instance.save()
        PostLog.objects.create(
            post=instance,
            action="Post Updated",
            comments=f"Post updated by {self.request.user.email}"
        )

    def perform_destroy(self, instance):
        PostLog.objects.create(
            post=instance,
            action="Post Deleted",
            comments=f"Post deleted by {instance.user.email}"
        )
        instance.delete()


class PostLogListView(generics.ListAPIView):
    queryset = PostLog.objects.all()
    serializer_class = PostLogSerializer
    permission_classes = [IsAuthenticated, IsDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return PostLog.objects.filter(post__user=self.request.user)


class CityListCreateView(generics.ListCreateAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticated]


class CityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'city_id'


class MatchDriverPostView(APIView):
    permission_classes = [IsAuthenticated, IsSender]
    authentication_classes = [JWTAuthentication]

    def post(self, request, post_id):
        try:
            post = DriverPost.objects.get(post_id=post_id, status__in=['Active', 'Booked'])
            PostLog.objects.create(
                post=post,
                action="Post Matched",
                comments=f"Post {post.post_id} matched by sender {request.user.email}"
            )
            return Response(
                {"message": f"Post {post_id} matched with a delivery"},
                status=status.HTTP_200_OK
            )
        except DriverPost.DoesNotExist:
            return Response(
                {"error": "Driver post not found or unavailable"},
                status=status.HTTP_404_NOT_FOUND
            )
