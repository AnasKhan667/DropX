import pytest
from driver_verification.models import DriverVerification, VerificationLog
from accounts.models import CustomUser

@pytest.mark.django_db
def test_driver_verification_creation():
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="123456"
    )

    verification = DriverVerification.objects.create(
        user=user,
        face_image="face_images/test.jpg",
        cnic_image="cnic_images/test.jpg"
    )

    assert verification.user == user
    assert verification.verification_status == "Pending"
    assert verification.face_verification_status is False
    assert verification.document_verification_status is False


@pytest.mark.django_db
def test_verification_log():
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="123456"
    )

    verification = DriverVerification.objects.create(
        user=user,
        face_image="face_images/test.jpg",
        cnic_image="cnic_images/test.jpg"
    )

    log = VerificationLog.objects.create(
        verification=verification,
        action="Test Action",
        comments="This is a test log."
    )

    assert log.verification == verification
    assert log.action == "Test Action"
