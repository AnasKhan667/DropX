from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import DriverVerification, VerificationLog
from .serializers import DriverVerificationSerializer, VerificationLogSerializer
from django.utils import timezone
from accounts.models import DriverProfile
import face_recognition
import os
import logging
import pickle
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
        verification = serializer.save(user=self.request.user)

        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_recognition_model.pkl')
        if not os.path.exists(model_path):
            logger.warning("Face model not found.")
            return

        try:
            with open(model_path, "rb") as f:
                face_model = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return

        try:
            driver_profile = self.request.user.driver_profile
        except DriverProfile.DoesNotExist:
            logger.error("DriverProfile not found.")
            return

        try:
            face_image = face_recognition.load_image_file(verification.face_image.path)
            face_encodings = face_recognition.face_encodings(face_image)

            if not face_encodings:
                verification.verification_status = "Rejected"
                verification.face_verification_status = False
                verification.failure_reason = "No face detected in uploaded image."
                verification.save()
                VerificationLog.objects.create(
                    verification=verification,
                    action="Face Verification Failed",
                    comments="No face detected in uploaded face image."
                )
                return

            predicted_name = face_model.predict([face_encodings[0]])[0].strip().lower()
            expected_name = self.request.user.first_name.strip().lower()
            is_match = predicted_name == expected_name

            verification.face_verification_status = is_match
            verification.verification_status = 'Verified' if is_match else 'Rejected'
            verification.verified_at = timezone.now() if is_match else None
            verification.failure_reason = None if is_match else "Face does not match the expected identity."

            if is_match:
                driver_profile.is_driver_verified = True
                driver_profile.save()

            verification.save()

            VerificationLog.objects.create(
                verification=verification,
                action="Face Verified" if is_match else "Face Verification Failed",
                comments=f"Predicted: {predicted_name}, Expected: {expected_name}, Match: {is_match}"
            )

        except Exception as e:
            logger.error(f"Auto-verification error: {str(e)}")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        verification = DriverVerification.objects.filter(user=request.user).latest('created_at')
        return Response({
            "message": "Face verification completed.",
            "status": verification.verification_status,
            "is_verified": verification.face_verification_status,
            "verified_at": verification.verified_at,
            "logs": VerificationLogSerializer(verification.logs.all(), many=True).data
        }, status=status.HTTP_201_CREATED)
    
class DriverVerificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DriverVerification.objects.all()
    serializer_class = DriverVerificationSerializer
    lookup_field = 'verification_id'
    permission_classes = [IsDriver]
    authentication_classes = [JWTAuthentication]

class VerificationLogListView(generics.ListAPIView):
    queryset = VerificationLog.objects.all()
    serializer_class = VerificationLogSerializer
    permission_classes = [IsDriver]
    authentication_classes = [JWTAuthentication]


# from rest_framework import generics, status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from .models import DriverVerification, VerificationLog
# from .serializers import DriverVerificationSerializer, VerificationLogSerializer
# from django.utils import timezone
# from accounts.models import DriverProfile
# import pytesseract
# from PIL import Image
# import face_recognition
# import os
# import logging
# import pickle
# from DropX.permissions import IsDriver, IsVerifiedDriver, IsSender
# from rest_framework_simplejwt.authentication import JWTAuthentication

# from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework_simplejwt.authentication import JWTAuthentication


# logger = logging.getLogger(__name__)


# class DriverVerificationListCreateView(generics.ListCreateAPIView):
#     queryset = DriverVerification.objects.all()
#     serializer_class = DriverVerificationSerializer
#     permission_classes = [IsDriver]
#     authentication_classes = [JWTAuthentication]
#     parser_classes = [MultiPartParser, FormParser]  # ✅ Needed for file uploads

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


# class DriverVerificationDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = DriverVerification.objects.all()
#     serializer_class = DriverVerificationSerializer
#     lookup_field = 'verification_id'
#     permission_classes = [IsDriver]
#     authentication_classes = [JWTAuthentication]

# class VerificationLogListView(generics.ListAPIView):
#     queryset = VerificationLog.objects.all()
#     serializer_class = VerificationLogSerializer
#     permission_classes = [IsDriver]
#     authentication_classes = [JWTAuthentication]

# class VerifyDriverView(APIView):
#     permission_classes = [IsDriver]
#     authentication_classes = [JWTAuthentication]

#     def __init__(self):
#         super().__init__()
#         self.face_model = None
#         model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_recognition_model.pkl')
#         if os.path.exists(model_path):
#             try:
#                 with open(model_path, "rb") as f:
#                     self.face_model = pickle.load(f)
#                 logger.info(f"Loaded face recognition model from {model_path}")
#             except Exception as e:
#                 logger.error(f"Failed to load face recognition model: {e}")
#         else:
#             logger.warning(f"Face recognition model not found at {model_path}; skipping face verification")

#     def post(self, request, verification_id):
#         try:
#             verification = DriverVerification.objects.get(verification_id=verification_id, user=request.user)
#         except DriverVerification.DoesNotExist:
#             logger.error(f"Verification ID {verification_id} not found for user {request.user.email}")
#             return Response({'error': 'Verification request not found'}, status=status.HTTP_404_NOT_FOUND)

#         try:
#             driver_profile = DriverProfile.objects.get(user=request.user)
#         except DriverProfile.DoesNotExist:
#             logger.error(f"DriverProfile not found for user {request.user.email}")
#             return Response({'error': 'Driver profile not found'}, status=status.HTTP_400_BAD_REQUEST)

#         # --- FACE VERIFICATION ONLY ---
#         try:
#             if not self.face_model:
#                 logger.error("Face recognition model is not loaded")
#                 return Response({'error': 'Face model not loaded'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             face_image = face_recognition.load_image_file(verification.face_image.path)
#             face_encodings = face_recognition.face_encodings(face_image)

#             if not face_encodings:
#                 logger.warning("No face detected in uploaded face image")
#                 VerificationLog.objects.create(
#                     verification=verification,
#                     action='Face Verification Failed',
#                     comments='No face detected in uploaded face image'
#                 )
#                 verification.verification_status = 'Rejected'
#                 verification.face_verification_status = False
#                 verification.save()
#                 return Response({'error': 'Face not detected in image'}, status=status.HTTP_400_BAD_REQUEST)

#             # Predict using the face model
#             predicted_name = self.face_model.predict([face_encodings[0]])[0]
#             user_prefix = request.user.email.split('@')[0]
#             is_match = predicted_name == user_prefix

#             verification.face_verification_status = is_match
#             verification.verification_status = 'Verified' if is_match else 'Rejected'
#             verification.verified_at = timezone.now() if is_match else None

#             VerificationLog.objects.create(
#                 verification=verification,
#                 action='Face Verified' if is_match else 'Face Verification Failed',
#                 comments=f'Predicted: {predicted_name}, Expected: {user_prefix}, Match: {is_match}'
#             )

#             if is_match:
#                 driver_profile.is_driver_verified = True
#                 driver_profile.save()

#             verification.save()
#             return Response(DriverVerificationSerializer(verification).data, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.error(f"Face verification error: {str(e)}")
#             return Response({'error': 'Face verification failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
