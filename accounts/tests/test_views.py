
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import CustomUser, DriverProfile, SenderProfile

@pytest.mark.django_db
def test_driver_registration_and_login():
    client = APIClient()
    url_register = reverse('accounts:driver-register')
    data = {
        'first_name': 'Test',
        'last_name': 'Driver',
        'email': 'testdriver@example.com',
        'phone_number': '+923001234573',
        'password': 'pass1234',
        'license_number': 'LIC99999'
    }
    # Register
    response = client.post(url_register, data, format='json')
    assert response.status_code == 201
    assert 'access' in response.data
    assert DriverProfile.objects.filter(user__email='testdriver@example.com').exists()

    # Login
    url_login = reverse('accounts:driver-login')
    login_data = {'email': 'testdriver@example.com', 'password': 'pass1234'}
    response = client.post(url_login, login_data, format='json')
    assert response.status_code == 200
    assert 'access' in response.data

@pytest.mark.django_db
def test_sender_registration_and_login():
    client = APIClient()
    url_register = reverse('accounts:sender-register')
    data = {
        'first_name': 'Test',
        'last_name': 'Sender',
        'email': 'testsender@example.com',
        'phone_number': '+923001234574',
        'password': 'pass1234'
    }
    response = client.post(url_register, data, format='json')
    assert response.status_code == 201
    assert SenderProfile.objects.filter(user__email='testsender@example.com').exists()

    url_login = reverse('accounts:sender-login')
    login_data = {'email': 'testsender@example.com', 'password': 'pass1234'}
    response = client.post(url_login, login_data, format='json')
    assert response.status_code == 200
