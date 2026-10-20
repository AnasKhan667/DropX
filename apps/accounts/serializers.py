from rest_framework import serializers
from .models import CustomUser, SenderProfile, DriverProfile, AuditLog
from phonenumber_field.serializerfields import PhoneNumberField
import re


class CustomUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    phone_number = PhoneNumberField()
    password = serializers.CharField(write_only=True)
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'address', 'role', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'password', 'license_number'
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined']

    # ============ FIELD VALIDATIONS ============
    
    def validate_password(self, value):
        """
        Password must have:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least 1 uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least 1 lowercase letter.")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least 1 digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least 1 special character (!@#$%^&*(),.?\":{}|<>).")
        return value

    def validate_first_name(self, value):
        """First name: only letters and spaces, min 2 characters"""
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        if not re.match(r'^[A-Za-z\s]+$', value):
            raise serializers.ValidationError("First name can only contain letters and spaces.")
        return value.strip().title()

    def validate_last_name(self, value):
        """Last name: only letters and spaces, min 2 characters"""
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        if not re.match(r'^[A-Za-z\s]+$', value):
            raise serializers.ValidationError("Last name can only contain letters and spaces.")
        return value.strip().title()

    def validate_email(self, value):
        """Normalize email to lowercase"""
        return value.lower().strip()

    def validate_license_number(self, value):
        """
        Pakistani CNIC-based license: 13 digits
        Accepts: 3520212345678 or 35202-1234567-8
        """
        if not value:
            return value
        
        # Remove dashes for validation
        clean_value = value.replace('-', '').replace(' ', '')
        
        if not clean_value.isdigit():
            raise serializers.ValidationError("License number must contain only digits.")
        
        if len(clean_value) != 13:
            raise serializers.ValidationError("License number must be exactly 13 digits (CNIC format).")
        
        # Check if already exists
        if DriverProfile.objects.filter(license_number=clean_value).exists():
            raise serializers.ValidationError("This license number is already registered.")
        
        return clean_value  # Store without dashes

    # ============ CROSS-FIELD VALIDATION ============
    
    def validate(self, data):
        """Validate license_number is provided for Driver role before user creation"""
        role = data.get('role')
        license_number = data.get('license_number', '')
        
        if role in ['Driver', 'Both'] and not license_number:
            raise serializers.ValidationError({
                'license_number': 'License number is required for Driver role.'
            })
        
        return data

    # ============ CREATE ============
    
    def create(self, validated_data):
        # Extract license_number before creating user
        license_number = validated_data.pop('license_number', None)
        password = validated_data.pop('password')
        role = validated_data.get('role')

        # User create
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )

        # Admin role handle
        if role == 'Admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()

        # Sender profile create
        if role in ['Sender', 'Both']:
            SenderProfile.objects.create(user=user)

        # Driver profile create
        if role in ['Driver', 'Both']:
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
        fields = ['id', 'user', 'license_number', 'is_driver_verified', 'wallet_balance', 'easypaisa_phone']


class AuditLogSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_email', 'action', 'details', 'timestamp']
