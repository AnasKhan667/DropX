from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Route
from .serializers import RouteSerializer

# List all routes and create a new route
class RouteListCreateView(generics.ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]

# Retrieve, update, or delete a specific route
class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]
