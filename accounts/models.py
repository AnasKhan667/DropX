from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[('Sender', 'Sender'), ('Driver', 'Driver'), ('Both', 'Both')],
        default='Sender'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class SenderProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='sender_profile')

    def __str__(self):
        return f"Sender: {self.user.email}"

class DriverProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=100, unique=True)
    is_driver_verified = models.BooleanField(default=False)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Driver: {self.user.email}"

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.email} at {self.timestamp}"