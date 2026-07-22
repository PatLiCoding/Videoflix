import django_rq
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from auth_app.models import User
from auth_app.api.tokens import account_activation_token


def send_activation_email(user, request):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = request.build_absolute_uri(
        f'/api/activate/{uidb64}/{token}/')
    queue = django_rq.get_queue('default')
    queue.enqueue(send_mail, 'Activate your account',
                  f'Click here to activate: {activation_link}',
                  settings.DEFAULT_FROM_EMAIL, [user.email],)


def send_password_confirm(user, request):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_link = request.build_absolute_uri(
        f'/api/password_confirm/{uidb64}/{token}/')
    queue = django_rq.get_queue('default')
    queue.enqueue(send_mail, 'Reset your password',
                  f'Click here to change your password: {activation_link}',
                  settings.DEFAULT_FROM_EMAIL, [user.email],)


def decode_uid(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
    return user
