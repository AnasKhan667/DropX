from rest_framework import serializers
from .models import CustomUser, SenderProfile, DriverProfile, AuditLog
from phonenumber_field.serializerfields import PhoneNumberField


class CustomUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    phone_number = PhoneNumberField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'address', 'role', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'password'
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined']

    def create(self, validated_data):
        request = self.context.get("request")
        license_number = request.data.get('license_number') if request else None

        password = validated_data.pop('password')
        role = validated_data.get('role')

        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )

        # Promote to admin if role = Admin
        if role == 'Admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()

        # Create profile based on role
        if role in ['Sender', 'Both']:
            SenderProfile.objects.create(user=user)

        if role in ['Driver', 'Both']:
            if not license_number:
                raise serializers.ValidationError("License number is required for Driver role.")
            DriverProfile.objects.create(user=user, license_number=license_number)

        return user


class SenderProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = SenderProfile
        fields = ['id', 'user']


class DriverProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = DriverProfile
        fields = ['id', 'user', 'license_number', 'is_driver_verified', 'wallet_balance']


class AuditLogSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_email', 'action', 'details', 'timestamp']
