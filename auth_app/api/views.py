"""API views for registration, activation, login, logout, token refresh,
and password reset/confirmation."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from django.contrib.auth.tokens import default_token_generator

from auth_app.models import User
from auth_app.api.serializers import RegistrationSerializer, \
    PasswordResetSerializer, PasswordConfirmSerializer
from auth_app.services.tokens import account_activation_token
from auth_app.services.email_utils import send_activation_email, \
    send_password_confirm
from auth_app.services.decode_uid import decode_uid
from auth_app.services.auth_services import generate_login_response, \
    get_validated_access_token, blacklist_refresh_token


class RegisterView(APIView):
    """Register a new, inactive user and send an activation email."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate registration data, create the user, and queue the
        activation email.

        Returns:
            Response: 201 with the created user's id/email on success.
        """
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_activation_email(user, request)
        return Response(
            {'user': {'id': user.id, 'email': user.email},
                'token': 'activation_token'},
            status=status.HTTP_201_CREATED)


class ActivateView(APIView):
    """Activate a user account via the emailed uid/token link."""
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Verify the uid/token pair and activate the matching account.

        Returns:
            Response: 200 on successful activation, 400 if the uid or
            token is invalid.
        """
        user = decode_uid(uidb64)
        if user is None:
            return Response({'message': 'Activation failed.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not account_activation_token.check_token(user, token):
            return Response({'message': 'Activation failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        return Response({'message': 'Account successfully activated.'},
                        status=status.HTTP_200_OK)


class LoginView(APIView):
    """Authenticate a user and issue JWT auth cookies."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and return a login response with cookies.

        Returns:
            Response: 200 with user info and access/refresh cookies set.
        """
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]
        user = serializer.user

        return generate_login_response(serializer, access, refresh, user)


class CookieTokenRefreshView(TokenRefreshView):
    """Issue a new access token cookie from a valid refresh token cookie."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Validate the refresh token cookie and set a new access cookie.

        Returns:
            Response: 200 with a new access_token cookie, 400 if no refresh
            token cookie is present, or 401 if it is invalid.
        """
        serializer_class = self.get_serializer_class()
        access_token, error_msg, error_status = get_validated_access_token(
            request, serializer_class)

        if error_msg:
            return Response(
                {"detail": error_msg}, status=error_status)

        response = Response(
            {"detail": "Token refreshed", "access": "new_access_token"})
        response.set_cookie(key="access_token", value=access_token,
                            httponly=True, secure=True, samesite="None")
        return response


class LogoutView(APIView):
    """Blacklist the refresh token and clear auth cookies."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Blacklist the current refresh token and delete auth cookies.

        Returns:
            Response: 200 on success, 401 if the refresh token is missing
            or invalid.
        """
        error_msg = blacklist_refresh_token(request)
        if error_msg:
            return Response(
                {"detail": error_msg}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"detail": (
            "Logout successful! All tokens will be deleted. "
            "Refresh token is now invalid.")}, status=status.HTTP_200_OK,)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class PasswordResetView(APIView):
    """Send a password-reset email for an existing account."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the email and queue a password-reset email.

        Returns:
            Response: 200 confirming an email was sent, 400 if the email
            is missing or unknown.
        """
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])
        send_password_confirm(user, request)
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK)


class PasswordConfirmView(APIView):
    """Confirm a password reset via the emailed uid/token link."""
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Verify the uid/token pair and set the user's new password.

        Returns:
            Response: 200 on successful reset, 400 if the uid, token, or
            new password data is invalid.
        """
        user = decode_uid(uidb64)
        if user is None:
            return Response({'detail': 'Password reset failed.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Password reset failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(
            {'detail': 'Your Password has been successfully reset.'},
            status=status.HTTP_200_OK)
