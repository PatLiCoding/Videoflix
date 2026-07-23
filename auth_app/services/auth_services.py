"""
Core utility actions for handling the token lifecycle.

This module houses processing algorithms that validate tokens extracted from
browser spaces, append blacklisted states, and set secured cookie values.
"""
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


def generate_login_response(serializer, access, refresh, user):
    """
    Helper function to generate a successful login response package.

    Sets both the access and refresh JWTs as secure HTTP-only cookies to
    shield them against Cross-Site Scripting (XSS) injection vectors.

    Args:
        serializer:
            The active validation serializer handling data structural
            evaluation.
        access (str):
            The raw string encrypted representation of the access token.
        refresh (str):
            The raw string encrypted representation of the refresh token.
        user:
            The validated User instance being authenticated.

    Returns:
        Response: A configured REST Framework response containing the user
                  data and the secured cookie headers.
    """
    if serializer.is_valid():
        response = Response(
            {"detail": "Login successful",
                "user": {"id": user.id, "username": user.email, },
             }, status=status.HTTP_200_OK,)
        response.set_cookie(key="access_token", value=access,
                            httponly=True, secure=True, samesite="Lax",)
        response.set_cookie(key="refresh_token", value=refresh,
                            httponly=True, secure=True, samesite="Lax",)
        return response
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


def get_validated_access_token(request, serializer_class):
    """
    Extracts the refresh token from the request cookies, validates it,
    and generates a new access token.

    Args:
        request:
            The active HTTP request instance object.
        serializer_class (type):
            The serializer class to process validation operations.

    Returns:
        tuple: (access_token, None) if successful, or (None, error_message)
               if validation fails.
    """
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return None, "Refresh token not found", status.HTTP_400_BAD_REQUEST

    serializer = serializer_class(data={"refresh": refresh_token})
    try:
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data.get("access"), None, None
    except (ValidationError, TokenError):
        return None, "Refresh token invalid", status.HTTP_401_UNAUTHORIZED


def blacklist_refresh_token(request):
    """
    Extracts the refresh token from the request cookies and blacklists it to
    prevent reuse.

    Guarantees that a compromised or old refresh token cannot be used again to
    gain access.

    Args:
        request: The active HTTP request context tracking execution.

    Returns:
        str or None: An error message string if the operation fails, or None
                     on success.
    """
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return "Token is invalid or expired"

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return None
    except TokenError:
        return "Token is invalid or expired"
