from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from auth_app.models import User


def decode_uid(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
    return user
