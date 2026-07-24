"""Utility for decoding a base64-encoded user ID back into a User instance."""
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from auth_app.models import User


def decode_uid(uidb64):
    """Decode a urlsafe base64 user ID and look up the matching user.

    Used by activation and password-reset links, which encode the user's
    primary key as part of the URL.

    Args:
        uidb64 (str): The urlsafe base64-encoded user primary key.

    Returns:
        User or None: The matching user instance, or None if the id is
        invalid or no matching user exists.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None
    return user
