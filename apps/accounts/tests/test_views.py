# import pytest
# from rest_framework.test import APIClient
# from django.urls import reverse
# from unittest.mock import patch
# from django.core.files.uploadedfile import SimpleUploadedFile

# @pytest.mark.django_db
# @patch("face_recognition.face_encodings", return_value=[[0.1, 0.2, 0.3]])
# @patch("face_recognition.compare_faces", return_value=[True])
# @patch("pytesseract.image_to_string", return_value="Name\nTest User\n12345 1234567 1")
# def test_driver_verification(mock1, mock2, mock3):
#     client = APIClient()

#     # --- Step 1: Register driver via API ---
#     url_register = reverse('accounts:driver-register')
#     register_data = {
#         'first_name': 'Test',
#         'last_name': 'Driver',
#         'email': 'testdriver@example.com',
#         'phone_number': '+923001234573',
#         'password': 'pass1234',
#         'license_number': 'LIC99999'
#     }
#     response = client.post(url_register, register_data, format='json')
#     assert response.status_code == 201
#     assert 'access' in response.data

#     # --- Step 2: Authenticate using JWT token returned by registration ---
#     token = response.data['access']
#     client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

#     # --- Step 3: Prepare in-memory fake images ---
#     face_file = SimpleUploadedFile("face.jpg", b"fake image content", content_type="image/jpeg")
#     cnic_file = SimpleUploadedFile("cnic.jpg", b"fake image content", content_type="image/jpeg")

#     # --- Step 4: Call driver verification endpoint ---
#     url_verification = reverse("driver-verification")
#     response = client.post(url_verification, {
#         "face_image": face_file,
#         "cnic_image": cnic_file
#     }, format="multipart")

#     # --- Step 5: Assertions ---
#     assert response.status_code == 201
#     assert response.data["status"] == "Verified"
#     assert response.data["is_face_verified"] is True
#     assert response.data["is_document_verified"] is True
#     assert response.data["cnic_number"] is not None
#     assert response.data["full_name"] == "Test User"
