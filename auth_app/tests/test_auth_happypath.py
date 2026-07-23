from auth_app.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from auth_app.services.tokens import account_activation_token
from django.contrib.auth.tokens import default_token_generator

from django.test import override_settings

RQ_QUEUES_TEST = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'ASYNC': False,
    },
}


@override_settings(
    RQ_QUEUES=RQ_QUEUES_TEST,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',)
class AuthTestsHappyPath(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='securepassword123')
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.refresh_token_url = reverse('token_refresh')
        self.password_reset_url = reverse('password_reset')

    def test_register_return_201(self):
        data = {"email": "user@example.com",
                "password": "securepassword",
                "confirmed_password": "securepassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_activate_user_return_200(self):
        data = {"email": "user@example.com",
                "password": "securepassword",
                "confirmed_password": "securepassword"}
        self.client.post(self.register_url, data, format='json')
        user = User.objects.get(email="user@example.com")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activate_url = reverse(
            'activate', kwargs={'uidb64': uidb64, 'token': token})
        response = self.client.get(activate_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_sets_jwt_cookies_return_200(self):
        data = {'email': 'test@example.com', 'password': 'securepassword123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        access_cookie = response.cookies['access_token']
        self.assertTrue(access_cookie['httponly'])
        self.assertEqual(access_cookie['samesite'], 'Lax')

    def test_logout_delete_jwt_cookies_return_200(self):
        login_data = {'email': 'test@example.com',
                      'password': 'securepassword123'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {}
        response = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_cookie = response.cookies.get('access_token')
        refresh_cookie = response.cookies.get('refresh_token')
        self.assertEqual(access_cookie.value, "")
        self.assertEqual(refresh_cookie.value, "")

    def test_refresh_token_return_200(self):
        login_data = {'email': 'test@example.com',
                      'password': 'securepassword123'}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {}
        response = self.client.post(
            self.refresh_token_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('detail'), "Token refreshed")

    def test_password_reset_return_200(self):
        data = {'email': 'test@example.com'}
        response = self.client.post(
            self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_confirm_return_200(self):
        data = {"new_password": "newsecurepassword",
                "confirm_password": "newsecurepassword"}
        user = User.objects.get(email="test@example.com")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        password_confirm_url = reverse(
            'password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
