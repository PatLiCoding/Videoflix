from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from auth_app.models import User
from auth_app.api.serializers import RegistrationSerializer
from auth_app.api.tokens import account_activation_token
from auth_app.api.utils import send_activation_email
from auth_app.api.services import generate_login_response, \
    get_validated_access_token, blacklist_refresh_token


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_activation_email(user, request)
        return Response(
            {'user': {'id': user.id, 'email': user.email},
                'token': 'activation_token'},
            status=status.HTTP_201_CREATED)


class ActivateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'message': 'Activation failed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account successfully activated.'},
                            status=status.HTTP_200_OK)

        return Response({'message': 'Activation failed.'},
                        status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]
        user = serializer.user

        return generate_login_response(serializer, access, refresh, user)


class CookieTokenRefreshView(TokenRefreshView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        access_token, error_msg, error_status = get_validated_access_token(
            request, serializer_class)

        if error_msg:
            return Response(
                {"detail": error_msg}, status=error_status)

        response = Response(
            {"detail": "Token refreshed", "access": "new_access_token"})
        response.set_cookie(key="access_token", value=access_token,
                            httponly=True, secure=True, samesite="Lax")
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        error_msg = blacklist_refresh_token(request)
        if error_msg:
            return Response(
                {"detail": error_msg},
                status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"detail": (
            "Logout successful! All tokens will be deleted. "
            "Refresh token is now invalid.")},
            status=status.HTTP_200_OK,)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
