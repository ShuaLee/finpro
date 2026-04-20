from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.middleware.csrf import CsrfViewMiddleware
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from typing import Any, cast
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.auth import clear_auth_cookies, set_auth_cookies
from apps.users.models import User
from apps.users.serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    EmailChangeConfirmSerializer,
    EmailChangeRequestSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
)
from apps.users.services import (
    AuthService,
    PasswordResetService,
)
from apps.users.views.base import ServiceAPIView


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


def enforce_csrf(request):
    check = _CSRFCheck(lambda _request: HttpResponse())
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise ValidationError("CSRF Failed: CSRF token missing or incorrect.")


class RegisterView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        user = AuthService.register_user(
            email=data["email"],
            password=data["password"],
            accept_terms=data["accept_terms"],
            full_name=data.get("full_name", ""),
            language=data.get("language", "en"),
            timezone_name=data.get("timezone", "UTC"),
            country=data.get("country", ""),
            currency=data.get("currency", "USD"),
            request=request,
        )

        return Response(
            {
                "detail": "Registration successful. Please verify your email.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        user, access, refresh = AuthService.login_user(
            email=data["email"],
            password=data["password"],
            request=request,
        )

        response = Response(
            {
                "detail": "Login successful.",
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, access, refresh)


class LogoutView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        refresh_cookie_name = settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh")
        refresh_token = data.get("refresh") or request.COOKIES.get(refresh_cookie_name)

        AuthService.logout_with_refresh_token(
            user=request.user,
            refresh_token=refresh_token,
            request=request,
        )

        response = Response(
            {"detail": "Logout successful."},
            status=status.HTTP_200_OK,
        )
        return clear_auth_cookies(response)


class LogoutAllSessionsView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        revoked_count = AuthService.logout_all_sessions(
            user=request.user,
            request=request,
        )

        response = Response(
            {
                "detail": "Logged out of all sessions.",
                "revoked_refresh_tokens": revoked_count,
            },
            status=status.HTTP_200_OK,
        )
        return clear_auth_cookies(response)


class DeleteAccountView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        deleted_email = AuthService.delete_account(
            user=request.user,
            current_password=data["current_password"],
            request=request,
        )

        response = Response(
            {
                "detail": "Account deleted successfully.",
                "email": deleted_email,
            },
            status=status.HTTP_200_OK,
        )
        return clear_auth_cookies(response)


class VerifyEmailView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        serializer = VerifyEmailSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        user = AuthService.verify_email_code(
            email=data["email"],
            code=data["code"],
            request=request,
        )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response(
            {
                "detail": "Email verified successfully.",
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, access, refresh)


class ResendVerificationView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        serializer = ResendVerificationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        user = User.objects.filter(email__iexact=data["email"]).first()
        if user:
            try:
                AuthService.resend_verification_for_user(user=user, request=request)
            except (ValidationError, DjangoValidationError):
                pass

        return Response(
            {"detail": "If the account exists, a verification email has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        serializer = PasswordResetRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        user = User.objects.filter(email__iexact=data["email"]).first()
        if user:
            PasswordResetService.request_for_email(user=user)

        return Response(
            {"detail": "If the account exists, a password reset email has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        serializer = PasswordResetConfirmSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        PasswordResetService.reset_with_token(
            raw_token=data["token"],
            new_password=data["new_password"],
        )

        return Response(
            {"detail": "Password reset successful."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        AuthService.change_password(
            user=request.user,
            current_password=data["current_password"],
            new_password=data["new_password"],
            request=request,
        )

        return Response(
            {"detail": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )


class EmailChangeRequestView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        target_email = AuthService.request_email_change(
            user=request.user,
            new_email=data["new_email"],
            current_password=data["current_password"],
            request=request,
        )

        return Response(
            {
                "detail": "Email change verification sent.",
                "target_email": target_email,
            },
            status=status.HTTP_200_OK,
        )


class EmailChangeConfirmView(ServiceAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeConfirmSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)

        user = AuthService.confirm_email_change(
            user=request.user,
            new_email=data["new_email"],
            code=data["code"],
            request=request,
        )

        return Response(
            {
                "detail": "Email changed successfully.",
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {"csrfToken": get_token(request)},
            status=status.HTTP_200_OK,
        )


class RefreshSessionView(ServiceAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        enforce_csrf(request)
        refresh_cookie_name = settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh")
        refresh_token = request.COOKIES.get(refresh_cookie_name)
        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data["access"]
        rotated_refresh_token = serializer.validated_data.get("refresh", refresh_token)

        response = Response(
            {"detail": "Session refreshed."},
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, access_token, rotated_refresh_token)
