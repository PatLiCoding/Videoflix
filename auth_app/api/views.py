from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from auth_app.models import User
from auth_app.api.serializers import RegistrationSerializer
from auth_app.api.tokens import account_activation_token
from auth_app.api.utils import send_activation_email
from auth_app.api.services import generate_login_response


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
