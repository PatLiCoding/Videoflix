"""Unhappy-path tests for the authentication API, covering 400/401/404
error responses across register, activate, login, logout, token refresh,
and password reset/confirm endpoints."""
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.test import override_settings
from django.contrib.auth.tokens import default_token_generator
from auth_app.services.tokens import account_activation_token
from auth_app.models import User

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
    """Verify that each auth endpoint fails correctly on invalid input."""

    def setUp(self):
        """Create a test user and resolve the auth endpoint URLs."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='securepassword123')
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.refresh_token_url = reverse('token_refresh')
        self.password_reset_url = reverse('password_reset')

    def test_register_mismatched_passwords_return_400(self):
        """400: Passwords do not match during registration."""
        data = {"email": "user@example.com",
                "password": "securepassword",
                "confirmed_password": "differentpassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_return_400(self):
        """400: Required field `email` is missing."""
        data = {"password": "securepassword",
                "confirmed_password": "securepassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email_return_400(self):
        """400: Registration with an email that is already in use."""
        data = {"email": "test@example.com",
                "password": "securepassword",
                "confirmed_password": "securepassword"}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_user_invalid_token_return_400(self):
        """400: Activation attempted with an invalid token."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = "invalid-token-12345"
        activate_url = reverse(
            'activate', kwargs={'uidb64': uidb64, 'token': invalid_token})
        response = self.client.get(activate_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_invalid_uid_return_400(self):
        """400: uidb64 points to a user that does not exist."""
        invalid_uidb64 = urlsafe_base64_encode(force_bytes(9999))
        activate_url = reverse('activate', kwargs={
            'uidb64': invalid_uidb64, 'token': 'irrelevant-token'})
        response = self.client.get(activate_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_already_active_user_return_400(self):
        """400: The same activation link is used a second time."""
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
        """400: Password is completely missing from the request body."""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_without_cookie_return_400(self):
        """400: Token refresh attempted without a refresh token cookie."""
        response = self.client.post(self.refresh_token_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_missing_email_return_400(self):
        """400: Required field `email` is missing for password reset."""
        response = self.client.post(self.password_reset_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_nonexistent_email_return_400(self):
        """400: Password reset requested for an email that does not exist."""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(
            self.password_reset_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_invalid_token_return_400(self):
        """400: Password reset confirmation with an invalid token."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = "invalid-token-12345"
        password_confirm_url = reverse('password_confirm', kwargs={
            'uidb64': uidb64, 'token': invalid_token})
        data = {"new_password": "newpassword123",
                "confirm_password": "newpassword123"}
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_invalid_uid_return_400(self):
        """400: uidb64 points to a user that does not exist."""
        invalid_uidb64 = urlsafe_base64_encode(force_bytes(9999))
        password_confirm_url = reverse('password_confirm', kwargs={
            'uidb64': invalid_uidb64, 'token': 'irrelevant-token'})
        data = {"new_password": "newpassword123",
                "confirm_password": "newpassword123"}
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_mismatched_passwords_return_400(self):
        """400: New password and its confirmation do not match."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        password_confirm_url = reverse(
            'password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        data = {"new_password": "newpassword123",
                "confirm_password": "differentpassword"}
        response = self.client.post(password_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_reused_token_return_400(self):
        """400: The same password-reset link is used a second time."""
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
        """401: Login attempted with an incorrect password."""
        data = {'email': 'test@example.com', 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_email_return_401(self):
        """401: Login attempted with an email that does not exist."""
        data = {'email': 'doesnotexist@example.com', 'password': 'whatever123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unactivated_user_return_401(self):
        """401: An inactive user attempts to log in."""
        self.user.is_active = False
        self.user.save()
        data = {'email': 'test@example.com', 'password': 'securepassword123'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_invalid_cookie_return_401(self):
        """
        401: Token refresh with a present but invalid refresh token cookie.
        """
        self.client.cookies['refresh_token'] = 'invalid-refresh-token-12345'
        response = self.client.post(self.refresh_token_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_cookie_return_401(self):
        """401: Logout attempted without a refresh token cookie."""
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_refresh_cookie_return_401(self):
        """401: Logout attempted with an invalid refresh token cookie."""
        self.client.cookies['refresh_token'] = 'invalid-refresh-token-12345'
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_endpoint_return_404(self):
        """404: Request to a route that does not exist."""
        response = self.client.get('/api/auth/does-not-exist/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
