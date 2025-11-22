import pytest
from accounts.models import CustomUser, SenderProfile, DriverProfile
from django.db import IntegrityError, transaction


@pytest.mark.django_db
def test_create_user_and_profiles():
    # create driver user
    driver_user = CustomUser.objects.create_user(
        email='driver@example.com',
        password='pass1234',
        first_name='John',
        last_name='Doe',
        phone_number='+923001234567',
        role='Driver'
    )
    DriverProfile.objects.create(user=driver_user, license_number='LIC12345')

    # create sender user
    sender_user = CustomUser.objects.create_user(
        email='sender@example.com',
        password='pass1234',
        first_name='Jane',
        last_name='Doe',
        phone_number='+923001234568',
        role='Sender'
    )
    SenderProfile.objects.create(user=sender_user)

    assert CustomUser.objects.count() == 2
    assert DriverProfile.objects.filter(user=driver_user).exists()
    assert SenderProfile.objects.filter(user=sender_user).exists()


@pytest.mark.django_db
def test_unique_email_and_phone():
    # Create initial user
    CustomUser.objects.create_user(
        email='unique@example.com',
        password='pass1234',
        first_name='A',
        last_name='B',
        phone_number='+923001234569'
    )

    # Test duplicate EMAIL
    with pytest.raises(IntegrityError):
        with transaction.atomic():   # isolate error
            CustomUser.objects.create_user(
                email='unique@example.com',
                password='pass1234',
                first_name='C',
                last_name='D',
                phone_number='+923001234570'
            )

    # Test duplicate PHONE NUMBER
    with pytest.raises(IntegrityError):
        with transaction.atomic():   # isolate error
            CustomUser.objects.create_user(
                email='another@example.com',
                password='pass1234',
                first_name='A',
                last_name='B',
                phone_number='+923001234569'
            )
