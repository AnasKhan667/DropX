# import pytest
# from accounts.serializers import CustomUserSerializer
# from accounts.models import CustomUser, DriverProfile, SenderProfile
# from rest_framework.exceptions import ValidationError
# from rest_framework import serializers

# @pytest.mark.django_db
# def test_serializer_create_driver_missing_license():
#     data = {
#         'first_name': 'Driver',
#         'last_name': 'User',
#         'email': 'driver_missing@example.com',
#         'phone_number': '+923001234580',
#         'password': 'pass1234',
#         'role': 'Driver'
#     }

#     class DummyRequest:
#         data = {}  # license_number missing

#     serializer = CustomUserSerializer(data=data, context={'request': DummyRequest()})
#     assert serializer.is_valid()
#     with pytest.raises(serializers.ValidationError) as exc_info:
#         serializer.save()  

#     assert "License number is required for Driver role." in str(exc_info.value)


# @pytest.mark.django_db
# def test_serializer_create_driver_success():
#     data = {
#         'first_name': 'Driver',
#         'last_name': 'User',
#         'email': 'driver3@example.com',
#         'phone_number': '+923001234573',
#         'password': 'pass1234',
#         'role': 'Driver'
#     }

#     class DummyRequest:
#         data = {'license_number': 'LIC56789'}

#     serializer = CustomUserSerializer(data=data, context={'request': DummyRequest()})
#     assert serializer.is_valid()
#     user = serializer.save()

#     assert user.email == 'driver3@example.com'
#     assert DriverProfile.objects.filter(user=user, license_number='LIC56789').exists()


# @pytest.mark.django_db
# def test_serializer_create_sender():
#     data = {
#         'first_name': 'Sender',
#         'last_name': 'User',
#         'email': 'sender2@example.com',
#         'phone_number': '+923001234572',
#         'password': 'pass1234',
#         'role': 'Sender'
#     }

#     serializer = CustomUserSerializer(data=data, context={'request': None})
#     assert serializer.is_valid()
#     user = serializer.save()
#     assert user.email == 'sender2@example.com'
#     assert SenderProfile.objects.filter(user=user).exists()
