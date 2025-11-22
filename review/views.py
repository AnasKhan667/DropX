from rest_framework import generics
from .models import Review
from .serializers import ReviewSerializer
from DropX.permissions import IsSender
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
