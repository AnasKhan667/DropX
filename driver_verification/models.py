from django.db import models
from accounts.models import CustomUser
import uuid
from django.utils import timezone

class DriverVerification(models.Model):
    verification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verifications')
    face_image = models.ImageField(upload_to='face_images/')
    cnic_image = models.ImageField(upload_to='cnic_images/')  # Added CNIC image

    # Status fields
    verification_status = models.CharField(
        max_length=50,
        choices=[('Pending', 'Pending'), ('Verified', 'Verified'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    face_verification_status = models.BooleanField(default=False)
    document_verification_status = models.BooleanField(default=False)  # CNIC verified
    failure_reason = models.CharField(max_length=255, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    cnic_number = models.CharField(max_length=20, null=True, blank=True)  # Extracted from CNIC
    full_name = models.CharField(max_length=100, null=True, blank=True)   # Extracted from CNIC
    formatted_text = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification {self.verification_id} for {self.user.email}"


class VerificationLog(models.Model):
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(DriverVerification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    comments = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.log_id} for Verification {self.verification.user.email}"
