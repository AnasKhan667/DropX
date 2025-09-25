# notification/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Notification
from delivery.models import Delivery, Package, DeliveryStatus
from accounts.models import CustomUser, DriverProfile
from driver_post.models import DriverPost, City
from vehicle.models import Vehicle
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sender = CustomUser.objects.create_user(
            email='rawad@gmail.com', password='pass', role='sender', id=uuid.uuid4()
        )
        self.driver = CustomUser.objects.create_user(
            email='anas@gmail.com', password='pass', role='driver', id=uuid.uuid4()
        )
        self.receiver = CustomUser.objects.create_user(
            email='receiver@example.com', password='pass', role='sender', id=uuid.uuid4()
        )
        DriverProfile.objects.create(user=self.driver, is_driver_verified=True)
        self.vehicle = Vehicle.objects.create(
            user=self.driver, vehicle_type_name='Car', max_capacity=500.0, max_weight=2000.0, status='approved'
        )
        self.city1 = City.objects.create(name='Peshawar', country='Pakistan', latitude=34.0151, longitude=71.5249)
        self.city2 = City.objects.create(name='Islamabad', country='Pakistan', latitude=33.6844, longitude=73.0479)
        self.post = DriverPost.objects.create(
            user=self.driver, vehicle=self.vehicle, start_city=self.city1, end_city=self.city2,
            start_latitude=34.0151, start_longitude=71.5249,
            end_latitude=33.6844, end_longitude=73.0479,
            departure_date='2025-09-25', departure_time='15:00:00', max_weight=2000.0
        )
        self.sender_token = str(RefreshToken.for_user(self.sender).access_token)
        self.receiver_token = str(RefreshToken.for_user(self.receiver).access_token)
        self.driver_token = str(RefreshToken.for_user(self.driver).access_token)
        self.delivery = Delivery.objects.create(
            sender_id=self.sender, receiver_id=self.receiver, driver_post_id=self.post,
            pickup_address={'address_line': 'Near Saddar Market', 'city': 'Peshawar', 'state': 'Khyber Pakhtunkhwa', 'country': 'Pakistan', 'latitude': 34.0151, 'longitude': 71.5805},
            dropoff_address={'address_line': 'G-10/1 Sector', 'city': 'Islamabad', 'state': 'Islamabad Capital Territory', 'country': 'Pakistan', 'latitude': 33.6844, 'longitude': 73.0479},
            pickup_city=self.city1, dropoff_city=self.city2,
            delivery_date='2025-09-25', estimated_delivery_time='2025-09-25T14:00:00Z', total_cost=0
        )
        Package.objects.create(
            delivery_id=self.delivery, description='Electronics', weight=20.55,
            dimensions={'length': 30, 'width': 20, 'height': 15}, is_fragile=True
        )

    def test_delivery_creation_notification(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.sender_token}')
        response = self.client.post('/api/delivery/create-with-cost/', {
            'driver_post_id': str(self.post.post_id),
            'receiver_id': str(self.receiver.id),
            'pickup_address': {
                'address_line': 'Near Saddar Market',
                'city': 'Peshawar',
                'state': 'Khyber Pakhtunkhwa',
                'country': 'Pakistan',
                'latitude': 34.0151,
                'longitude': 71.5805
            },
            'dropoff_address': {
                'address_line': 'G-10/1 Sector',
                'city': 'Islamabad',
                'state': 'Islamabad Capital Territory',
                'country': 'Pakistan',
                'latitude': 33.6844,
                'longitude': 73.0479
            },
            'delivery_date': '2025-09-25',
            'estimated_delivery_time': '2025-09-25T14:00:00Z',
            'packages': [
                {'description': 'Electronics', 'weight': 20.55, 'dimensions': {'length': 30, 'width': 20, 'height': 15}, 'is_fragile': True}
            ]
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.filter(user_id=self.sender, type='Delivery Created').count(), 1)
        self.assertEqual(Notification.objects.filter(user_id=self.receiver, type='Delivery Created').count(), 1)

    def test_delivery_accept_notification(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.driver_token}')
        response = self.client.post(f'/api/delivery/accept/{self.delivery.delivery_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user_id=self.sender, type='Delivery Accepted').count(), 1)
        self.assertEqual(Notification.objects.filter(user_id=self.receiver, type='Delivery Accepted').count(), 1)

    def test_list_notifications(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.sender_token}')
        response = self.client.get('/api/notification/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'Delivery Created')

    def test_mark_notification_read(self):
        notification = Notification.objects.get(user_id=self.sender, delivery_id=self.delivery)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.sender_token}')
        response = self.client.post(f'/api/notification/mark-read/{notification.notification_id}/')
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_notifications_read(self):
        Notification.objects.create(
            user_id=self.sender, delivery_id=self.delivery,
            type='Test', message='Test notification', is_read=False
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.sender_token}')
        response = self.client.post('/api/notification/mark-all-read/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user_id=self.sender, is_read=False).count(), 0)