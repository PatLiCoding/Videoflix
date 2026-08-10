"""
Custom Authentication Backend configurations.

This module overrides the standard token lookup locations used by Django REST
Framework to adapt them to secure, cookie-centric architectures.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom authentication class that ensures SimpleJWT extracts the access
    token from cookies.

    Overrides the default header validation lookup, enabling transparent,
    token-based browser authentication without exposing tokens to frontend
    JavaScript layers.
    """

    def authenticate(self, request):
        """
        Extract the access token from the request cookies and authenticate
        the user.

        Args:
            request: The current inbound HTTP request context container.

        Returns:
            tuple:
                A tuple containing (user, validated_token) if authentication
                succeeds.
            None:
                If no access token is provided within the cookies.
        """
        raw_token = request.COOKIES.get('access_token')

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
