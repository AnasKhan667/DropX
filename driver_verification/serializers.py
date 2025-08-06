from rest_framework import serializers
from .models import DriverVerification, VerificationLog
from accounts.serializers import CustomUserSerializer

class VerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationLog
        fields = ['log_id', 'verification', 'action', 'comments', 'timestamp']
        read_only_fields = ['log_id', 'timestamp']

class DriverVerificationSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    logs = VerificationLogSerializer(many=True, read_only=True)
    face_image = serializers.ImageField(required=True)

    class Meta:
        model = DriverVerification
        fields = [
            'verification_id', 'user', 'face_image',
            'face_verification_status', 'verification_status',
            'verified_at', 'failure_reason', 'logs'
        ]
        read_only_fields = [
            'verification_id', 'user', 'face_verification_status',
            'verification_status', 'verified_at', 'failure_reason', 'logs'
        ]
