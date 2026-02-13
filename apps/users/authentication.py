from django.conf import settings
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
        cookie_key = settings.SIMPLE_JWT.get("AUTH_COOKIE", "access")
        access_token = request.COOKIES.get(cookie_key)

        if not access_token:
            return None  # No token cookie -> unauthenticated request

        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            raise AuthenticationFailed("Invalid token in cookie")