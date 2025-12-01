from rest_framework import generics
from .models import Review
from .serializers import ReviewSerializer
from DropX.permissions import IsSender, IsDriver
from rest_framework_simplejwt.authentication import JWTAuthentication

class ReviewCreateView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsSender]
    authentication_classes = [JWTAuthentication]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class ReviewDetailView(generics.RetrieveAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    lookup_field = "review_id"
    permission_classes = [IsSender]
    authentication_classes = [JWTAuthentication]


class DriverReviewsListView(generics.ListAPIView):
    """Driver can see all reviews received for their deliveries"""
    serializer_class = ReviewSerializer
    permission_classes = [IsDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Review.objects.filter(reviewed_id=self.request.user).order_by('-created_at')
