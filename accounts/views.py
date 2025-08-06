from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import CustomUser, AuditLog
from .serializers import CustomUserSerializer, AuditLogSerializer
import logging

logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = CustomUserSerializer(self.user).data
        return data

class DriverLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.warning(f"Failed driver login attempt for email {request.data.get('email')}: {str(e)}")
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.user
        if user.role not in ['Driver', 'Both']:
            logger.warning(f"User {user.email} attempted driver login but role is {user.role}")
            return Response({'error': 'Not a driver'}, status=status.HTTP_403_FORBIDDEN)

        AuditLog.objects.create(
            user=user,
            action='Driver Login',
            details=f"Driver {user.email} logged in successfully"
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class SenderLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.warning(f"Failed sender login attempt for email {request.data.get('email')}: {str(e)}")
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.user
        if user.role not in ['Sender', 'Both']:
            logger.warning(f"User {user.email} attempted sender login but role is {user.role}")
            return Response({'error': 'Not a sender'}, status=status.HTTP_403_FORBIDDEN)

        AuditLog.objects.create(
            user=user,
            action='Sender Login',
            details=f"Sender {user.email} logged in successfully"
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class DriverRegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['first_name', 'last_name', 'email', 'phone_number', 'password', 'license_number'],
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'license_number': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={201: CustomUserSerializer()}
    )
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'Driver'
        serializer = CustomUserSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            AuditLog.objects.create(
                user=user,
                action='Driver Registered',
                details=f"Driver {user.email} registered successfully"
            )
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        logger.error(f"Driver registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SenderRegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['first_name', 'last_name', 'email', 'phone_number', 'password'],
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD)
            }
        ),
        responses={201: CustomUserSerializer()}
    )
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'Sender'
        serializer = CustomUserSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            AuditLog.objects.create(
                user=user,
                action='Sender Registered',
                details=f"Sender {user.email} registered successfully"
            )
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        logger.error(f"Sender registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListCreateView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="User ID",
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            AuditLog.objects.create(
                user=request.user,
                action='Logout',
                details=f"User {request.user.email} logged out successfully"
            )
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(f"Logout failed for {request.user.email}: {str(e)}")
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)