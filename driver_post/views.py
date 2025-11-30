from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from .models import DriverPost, City, PostLog
from .serializers import DriverPostSerializer, CitySerializer, PostLogSerializer, DriverPostUpdateSerializer
from accounts.models import DriverProfile
from DropX.permissions import IsDriver, IsVerifiedDriver, IsSender
import logging
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

logger = logging.getLogger(__name__)

MAX_USERS_PER_POST = 3  # max allowed senders per post


def auto_expire_posts():
    today = timezone.now().date()
    expired_posts = DriverPost.objects.filter(
        departure_date__lt=today,
        status__in=["Active", "Booked"]
    )
    for post in expired_posts:
        post.status = "Expired"
        post.save()

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

    # ✅ Pass request in serializer context
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        auto_expire_posts()
        if self.request.user.role == 'driver':
            return DriverPost.objects.filter(user=self.request.user)
        return DriverPost.objects.filter(status__in=['Active', 'Booked'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(DriverPostSerializer(serializer.instance, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        try:
            driver_profile = self.request.user.driver_profile
            if not driver_profile.is_driver_verified:
                raise PermissionDenied("Only verified drivers can create posts.")
            if not self.request.user.vehicles.filter(status='approved').exists():
                raise ValidationError("You must have an approved vehicle to create a post.")

            serializer.save(user=self.request.user)

            PostLog.objects.create(
                post=serializer.instance,
                action="Post Created",
                comments=f"Post created by {self.request.user.email} from {serializer.instance.start_city} to {serializer.instance.end_city}"
            )

        except DriverProfile.DoesNotExist:
            raise ValidationError("Driver profile not found.")

class DriverPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DriverPost.objects.all()
    lookup_field = 'post_id'
    permission_classes = [IsAuthenticated, IsDriver]
    authentication_classes = [JWTAuthentication]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    # ✔ Use update serializer for PUT/PATCH
    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DriverPostUpdateSerializer
        return DriverPostSerializer

    def get_queryset(self):
        auto_expire_posts()
        return DriverPost.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.instance
        serializer.save()
        if instance.departure_date < timezone.now().date():
            instance.status = "Expired"
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
        auto_expire_posts()
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
        auto_expire_posts()
        try:
            post = DriverPost.objects.get(post_id=post_id, status__in=['Active', 'Booked'])

            current_matches = PostLog.objects.filter(post=post, action="Post Matched").count()
            if current_matches >= MAX_USERS_PER_POST:
                return Response(
                    {"error": f"This post has reached maximum bookings ({MAX_USERS_PER_POST})"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            PostLog.objects.create(
                post=post,
                action="Post Matched",
                comments=f"Post {post.post_id} matched by sender {request.user.email}"
            )

            if current_matches + 1 >= MAX_USERS_PER_POST:
                post.status = "Booked"
                post.save()

            return Response(
                {"message": f"Post {post_id} matched successfully"},
                status=status.HTTP_200_OK
            )

        except DriverPost.DoesNotExist:
            return Response(
                {"error": "Driver post not found or unavailable"},
                status=status.HTTP_404_NOT_FOUND
            )
