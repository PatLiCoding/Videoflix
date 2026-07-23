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
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class AuthTestsUnhappyPath(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='securepassword123')
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.refresh_token_url = reverse('token_refresh')
        self.password_reset_url = reverse('password_reset')

    def test_register_mismatched_passwords_return_400(self):
        """400: Passwörter stimmen bei der Registrierung nicht überein."""
        data = {"email": "user@example.com",
                "password": "securepassword",
                "confirmed_password": "differentpassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_return_400(self):
        """400: Pflichtfeld email fehlt."""
        data = {"password": "securepassword",
                "confirmed_password": "securepassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email_return_400(self):
        """400: Registrierung mit bereits existierender Email."""
        data = {"email": "test@example.com",
                "password": "securepassword",
                "confirmed_password": "securepassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_user_invalid_token_return_400(self):
        """400: Aktivierung mit einem ungültigen Token/UID."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = "invalid-token-12345"
        activate_url = reverse(
            'activate', kwargs={'uidb64': uidb64, 'token': invalid_token})
        response = self.client.get(activate_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_invalid_uid_return_400(self):
        """400: uidb64 zeigt auf einen User, den es nicht gibt."""
        invalid_uidb64 = urlsafe_base64_encode(force_bytes(9999))
        activate_url = reverse('activate', kwargs={
            'uidb64': invalid_uidb64, 'token': 'irrelevant-token'})
        response = self.client.get(activate_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_already_active_user_return_400(self):
        """400: derselbe Aktivierungslink wird ein zweites Mal benutzt."""
        data = {"email": "user2@example.com", "password": "securepassword123",
                "confirmed_password": "securepassword123"}
        self.client.post(self.register_url, data, format='json')
        user = User.objects.get(email="user2@example.com")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activate_url = reverse(
            'activate', kwargs={'uidb64': uidb64, 'token': token})
        first_response = self.client.get(activate_url, format='json')
        self.assertEqual(
            first_response.status_code, status.HTTP_200_OK)
        second_response = self.client.get(activate_url, format='json')
        self.assertEqual(
            second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password_return_400(self):
        """400: Passwort fehlt komplett im Request Body."""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_without_cookie_return_400(self):
        """400: Token-Refresh ohne Refresh-Token-Cookie."""
        response = self.client.post(self.refresh_token_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_missing_email_return_400(self):
        """400: Pflichtfeld email fehlt beim Passwort-Reset."""
        response = self.client.post(self.password_reset_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_nonexistent_email_return_400(self):
        """400: Passwort-Reset für eine nicht existierende E-Mail anfordern."""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(
            self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_invalid_token_return_400(self):
        """400: Passwort-Reset mit einem ungültigen Token."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = "invalid-token-12345"
        password_confirm_url = reverse('password_confirm', kwargs={
            'uidb64': uidb64, 'token': invalid_token})
        data = {"new_password": "newpassword123",
                "confirm_password": "newpassword123"}
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_invalid_uid_return_400(self):
        """400: uidb64 zeigt auf einen User, den es nicht gibt."""
        invalid_uidb64 = urlsafe_base64_encode(force_bytes(9999))
        password_confirm_url = reverse('password_confirm', kwargs={
            'uidb64': invalid_uidb64, 'token': 'irrelevant-token'})
        data = {"new_password": "newpassword123",
                "confirm_password": "newpassword123"}
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_mismatched_passwords_return_400(self):
        """400: Neues Passwort und Bestätigung stimmen nicht überein."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        password_confirm_url = reverse(
            'password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        data = {"new_password": "newpassword123",
                "confirm_password": "differentpassword"}
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_reused_token_return_400(self):
        """400: derselbe Passwort-Reset-Link wird ein zweites Mal benutzt."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        password_confirm_url = reverse(
            'password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        first_data = {"new_password": "firstnewpassword123",
                      "confirm_password": "firstnewpassword123"}
        first_response = self.client.post(
            password_confirm_url, first_data, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        second_data = {"new_password": "secondnewpassword123",
                       "confirm_password": "secondnewpassword123"}
        second_response = self.client.post(
            password_confirm_url, second_data, format='json')
        self.assertEqual(
            second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_credentials_return_401(self):
        """401: Login mit falschem Passwort."""
        data = {'email': 'test@example.com', 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_email_return_401(self):
        """401: Login mit einer Email, die es gar nicht gibt."""
        data = {'email': 'doesnotexist@example.com', 'password': 'whatever123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unactivated_user_return_401(self):
        """401: Inaktiver Benutzer versucht sich einzuloggen."""
        self.user.is_active = False
        self.user.save()
        data = {'email': 'test@example.com', 'password': 'securepassword123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_invalid_cookie_return_401(self):
        """401: Token-Refresh mit einem vorhandenen, aber ungültigen Refresh-Token-Cookie."""
        self.client.cookies['refresh_token'] = 'invalid-refresh-token-12345'
        response = self.client.post(self.refresh_token_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_cookie_return_401(self):
        """401: Logout-Versuch ohne Refresh-Token-Cookie."""
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_refresh_cookie_return_401(self):
        """401: Logout-Versuch mit einem ungültigen Refresh-Token-Cookie."""
        self.client.cookies['refresh_token'] = 'invalid-refresh-token-12345'
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_endpoint_return_404(self):
        """404: Anfrage an eine Route, die es gar nicht gibt."""
        response = self.client.get('/api/auth/does-not-exist/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
