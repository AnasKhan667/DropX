import pytest
from rest_framework.test import APIClient
from accounts.models import CustomUser, DriverProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from unittest.mock import patch
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

@pytest.mark.django_db
@patch("face_recognition.face_encodings", return_value=[[0.1, 0.2, 0.3]])
@patch("face_recognition.compare_faces", return_value=[True])
@patch("pytesseract.image_to_string", return_value="Name\nTest User\n12345 1234567 1")
def test_driver_verification(mock1, mock2, mock3):
    client = APIClient()

    # 1️⃣ Create unique user
    unique_id = str(uuid.uuid4())[:8]
    user = CustomUser.objects.create_user(
        email=f"testdriver_{unique_id}@example.com",
        password="pass1234",
        first_name=f"Test{unique_id}",
        last_name=f"Driver{unique_id}",
        phone_number=f"+92300{unique_id}99",
    )

    # 2️⃣ Set is_driver=True if required by permission class
    user.is_driver = True
    user.save()

    # 3️⃣ Create driver profile
    DriverProfile.objects.create(
        user=user,
        license_number=f"LIC{unique_id}",
        is_driver_verified=True
    )

    # 4️⃣ Generate JWT token and set header
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # 5️⃣ Prepare in-memory fake images
    face_file = SimpleUploadedFile("face.jpg", b"fake image content", content_type="image/jpeg")
    cnic_file = SimpleUploadedFile("cnic.jpg", b"fake image content", content_type="image/jpeg")

    # 6️⃣ Call verification endpoint
    url = reverse("driver-verification")
    response = client.post(url, {
        "face_image": face_file,
        "cnic_image": cnic_file
    }, format="multipart")

    # 7️⃣ Debug prints
    print("User:", user.email)
    print("Is authenticated?", user.is_authenticated)
    print("Has driver_profile?", hasattr(user, 'driver_profile'))
    print("Driver verified?", getattr(user.driver_profile, 'is_driver_verified', None))
    print("Response status:", response.status_code)
    print("Response data:", response.data)

    # 8️⃣ Assertions
    assert response.status_code == 201
    assert response.data["status"] == "Verified"
    assert response.data["is_face_verified"] is True
    assert response.data["is_document_verified"] is True
    assert response.data["cnic_number"] is not None
    assert response.data["full_name"] == "Test User"
