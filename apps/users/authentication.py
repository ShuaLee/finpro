"""
users.authentication
~~~~~~~~~~~~~~~~~~~~
Provides custom authentication classes for JWT-based login using cookies.
This helps implement secure session-like behavior for APIs.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTFromCookieAuthentication(JWTAuthentication):
    """
    Custom authentication class for Django REST Framework that reads JWT tokens from cookies.

    By default, DRF SimpleJWT expects JWT tokens in the Authorization header.
    This class overrides that behavior to:
    - Look for the 'access' token inside HTTP cookies.
    - Validate the token and return the associated user.

    Use Case:
        Ideal for frontend apps using HttpOnly cookies for authentication instead of headers.
    """

    def authenticate(self, request):
        """
        Authenticate the request using the JWT access token stored in cookies.

        Args:
            request (Request): The incoming DRF request object.

        Returns:
            tuple: (user, validated_token) if authentication succeeds.
            None: If no token is found (authentication will be skipped).

        Raises:
            AuthenticationFailed: If the token exists but is invalid.
        """
        access_token = request.COOKIES.get("access")
        if not access_token:
            return None  # No token found in cookie

        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            raise AuthenticationFailed("Invalid token in cookie")
