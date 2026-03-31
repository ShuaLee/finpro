from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


class JWTFromCookieAuthentication(JWTAuthentication):
    """Authenticate using the access token stored in HttpOnly cookies."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

    def _enforce_csrf(self, request):
        check = _CSRFCheck(lambda _request: HttpResponse())
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise AuthenticationFailed(
                "CSRF Failed: CSRF token missing or incorrect.")

    def authenticate(self, request):
        cookie_key = settings.SIMPLE_JWT.get("AUTH_COOKIE", "access")
        access_token = request.COOKIES.get(cookie_key)

        if not access_token:
            return None

        try:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
        except Exception as exc:
            raise AuthenticationFailed("Invalid token in cookie") from exc

        if request.method not in self.SAFE_METHODS:
            self._enforce_csrf(request)

        return user, validated_token
