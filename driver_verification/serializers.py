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
    cnic_image = serializers.ImageField(required=True)
    formatted_text = serializers.CharField(read_only=True)  # new field

    class Meta:
        model = DriverVerification
        fields = [
            'verification_id', 'user', 'face_image', 'cnic_image',
            'face_verification_status', 'document_verification_status',
            'verification_status', 'verified_at', 'failure_reason',
            'cnic_number', 'full_name', 'logs', 'formatted_text'
        ]
        read_only_fields = [
            'verification_id', 'user', 'face_verification_status', 'document_verification_status',
            'verification_status', 'verified_at', 'failure_reason',
            'cnic_number', 'full_name', 'logs', 'formatted_text'
        ]
