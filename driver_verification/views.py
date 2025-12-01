from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import DriverVerification, VerificationLog
from .serializers import DriverVerificationSerializer, VerificationLogSerializer
from django.utils import timezone
from accounts.models import DriverProfile
import face_recognition
import pytesseract
import cv2
import re
from PIL import Image
import logging
from DropX.permissions import IsDriver
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

class DriverVerificationListCreateView(generics.ListCreateAPIView):
    queryset = DriverVerification.objects.all()
    serializer_class = DriverVerificationSerializer
    permission_classes = [IsDriver]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        # Check if user already has a pending or verified verification
        existing = DriverVerification.objects.filter(
            user=self.request.user,
            verification_status__in=["Pending", "Verified"]
        ).exists()
        if existing:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You already have a pending or approved verification request.")
        
        verification = serializer.save(user=self.request.user)

        try:
            # --- FACE VERIFICATION ---
            cnic_image = face_recognition.load_image_file(verification.cnic_image.path)
            face_image = face_recognition.load_image_file(verification.face_image.path)

            cnic_faces = face_recognition.face_encodings(cnic_image)
            face_faces = face_recognition.face_encodings(face_image)

            if not cnic_faces or not face_faces:
                verification.verification_status = "Rejected"
                verification.face_verification_status = False
                verification.failure_reason = "Face not detected in one of the images."
                verification.save()
                VerificationLog.objects.create(
                    verification=verification,
                    action="Face Verification Failed",
                    comments="No face detected in uploaded images."
                )
                return

            is_face_match = face_recognition.compare_faces([cnic_faces[0]], face_faces[0])[0]
            verification.face_verification_status = is_face_match

            if is_face_match:

                # --- CNIC OCR EXTRACTION ---
                image_bgr = cv2.imread(verification.cnic_image.path)
                gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
                raw_text = pytesseract.image_to_string(gray)

                # Store formatted OCR text
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                verification.formatted_text = '\n'.join(lines)

                text_normalized = re.sub(r'[^0-9A-Za-z\s]', '', raw_text)

                # Extract CNIC number
                cnic_candidate = re.findall(r'\d{5}\s*\d{7}\s*\d', text_normalized)
                verification.cnic_number = cnic_candidate[0] if cnic_candidate else None

                # --- 🔥 PREVENT MULTIPLE ACCOUNTS USING SAME CNIC ---
                if verification.cnic_number:
                    duplicate = DriverVerification.objects.filter(
                        cnic_number=verification.cnic_number,
                        verification_status="Verified"
                    ).exclude(user=self.request.user)

                    if duplicate.exists():
                        verification.verification_status = "Rejected"
                        verification.document_verification_status = False
                        verification.failure_reason = "This CNIC is already verified by another user."
                        verification.save()

                        VerificationLog.objects.create(
                            verification=verification,
                            action="CNIC Duplicate Blocked",
                            comments="CNIC already used by another verified driver."
                        )
                        return

                # Extract Name
                name = None
                for i, line in enumerate(lines):
                    if 'Name' in line or 'NAME' in line:
                        if i + 1 < len(lines):
                            name = lines[i + 1]
                        break

                verification.full_name = name

                # FINAL DECISION - Both CNIC number and Name must be extracted
                if verification.cnic_number and verification.full_name:
                    verification.document_verification_status = True
                    verification.verification_status = "Verified"
                    verification.verified_at = timezone.now()
                else:
                    verification.document_verification_status = False
                    verification.verification_status = "Rejected"
                    # Specific failure reason
                    missing = []
                    if not verification.cnic_number:
                        missing.append("CNIC number")
                    if not verification.full_name:
                        missing.append("Name")
                    verification.failure_reason = f"Could not extract {' and '.join(missing)} from CNIC image. Please upload a clearer image."

            else:
                verification.verification_status = "Rejected"
                verification.failure_reason = "Face did not match."

            verification.save()

            # --- UPDATE DRIVER PROFILE IF VERIFIED ---
            if verification.verification_status == "Verified":
                driver_profile = getattr(self.request.user, 'driver_profile', None)
                if driver_profile:
                    driver_profile.is_driver_verified = True
                    driver_profile.save()

            # LOGGING
            VerificationLog.objects.create(
                verification=verification,
                action="Verification Passed" if verification.verification_status == "Verified" else "Verification Failed",
                comments=f"Face match: {is_face_match}, CNIC: {verification.cnic_number}, Name: {verification.full_name}"
            )

        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            verification.verification_status = "Rejected"
            verification.failure_reason = str(e)
            verification.save()
            VerificationLog.objects.create(
                verification=verification,
                action="Verification Error",
                comments=str(e)
            )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        verification = DriverVerification.objects.filter(user=request.user).latest('created_at')
        return Response({
            "message": "Verification processed.",
            "status": verification.verification_status,
            "is_face_verified": verification.face_verification_status,
            "is_document_verified": verification.document_verification_status,
            "cnic_number": verification.cnic_number,
            "full_name": verification.full_name,
            "formatted_text": verification.formatted_text,
            "logs": VerificationLogSerializer(verification.logs.all(), many=True).data
        }, status=status.HTTP_201_CREATED)


class VerificationLogListView(generics.ListAPIView):
    serializer_class = VerificationLogSerializer
    permission_classes = [IsDriver]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        # Only return logs for verifications belonging to the current user
        return VerificationLog.objects.filter(verification__user=self.request.user).order_by('-timestamp')
