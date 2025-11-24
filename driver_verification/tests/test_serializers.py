
from driver_verification.serializers import DriverVerificationSerializer
from driver_verification.models import DriverVerification
from accounts.models import CustomUser
import pytest

@pytest.mark.django_db
def test_driver_verification_serializer():
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="123456"
    )

    verification = DriverVerification.objects.create(
        user=user,
        face_image="face_images/test.jpg",
        cnic_image="cnic_images/test.jpg"
    )

    serializer = DriverVerificationSerializer(instance=verification)
    data = serializer.data

    assert data["verification_id"] is not None
    assert data["user"]["email"] == "test@example.com"
    assert data["face_image"] is not None
    assert data["cnic_image"] is not None
