from django.shortcuts import render
from rest_framework import generics
from .models import Review
from .serializers import ReviewSerializer
from DropX.permissions import IsSender

# Create your views here.
class ReviewCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsSender]

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    lookup_field = 'review_id'
    permission_classes = [IsSender]
    
