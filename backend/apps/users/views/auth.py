from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from users.cookie import clear_auth_cookies, set_auth_cookies, set_trusted_device_cookie
from users.serializers.auth import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginCodeVerifySerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
)
from users.services import (
    AuthService,
    EmailVerificationService,
    LoginSecurityCodeService,
    PasswordResetService,
    TrustedDeviceService,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthService.register_user(**serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Registration successful. Enter the verification code sent to your email.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = EmailVerificationService.verify_email_code(
                email=serializer.validated_data["email"],
                code=serializer.validated_data["code"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        response = Response(
            {"detail": "Email verified.", "email": user.email},
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, access, refresh)


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from users.models import User

        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if not user:
            return Response(
                {"detail": "If this email exists, a verification email was sent."},
                status=status.HTTP_200_OK,
            )

        try:
            EmailVerificationService.resend_for_user(user=user)
        except DjangoValidationError:
            pass

        return Response(
            {"detail": "If this email exists, a verification email was sent."},
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from users.models import User

        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()

        # Always return success to avoid account enumeration
        if not user:
            return Response(
                {"detail": "If this email exists, a reset email was sent."},
                status=status.HTTP_200_OK,
            )

        try:
            PasswordResetService.request_for_email(user=user)
        except DjangoValidationError:
            pass

        return Response(
            {"detail": "If this email exists, a reset email was sent."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            PasswordResetService.reset_with_token(
                raw_token=serializer.validated_data["token"],
                new_password=serializer.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Password reset successful."}, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthService.authenticate_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        if TrustedDeviceService.is_request_trusted_for_user(request=request, user=user):
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            response = Response(
                {"detail": "Login successful.", "email": user.email},
                status=status.HTTP_200_OK,
            )
            return set_auth_cookies(response, access, refresh)

        try:
            LoginSecurityCodeService.issue_and_send(user=user)
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Security code sent to your email.",
                "requires_login_code": True,
                "email": user.email,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class VerifyLoginCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginCodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = LoginSecurityCodeService.verify_code(
                email=serializer.validated_data["email"],
                code=serializer.validated_data["code"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        response = Response(
            {"detail": "Login successful.", "email": user.email},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, access, refresh)

        if serializer.validated_data.get("remember_device"):
            trusted_raw = TrustedDeviceService.issue_for_user(user=user)
            set_trusted_device_cookie(response, trusted_raw)

        return response


class RefreshSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie_key = settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh")
        refresh_token = request.COOKIES.get(refresh_cookie_key)

        if not refresh_token:
            return Response({"detail": "No refresh token provided."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        access = serializer.validated_data["access"]
        refresh = serializer.validated_data.get("refresh", refresh_token)

        response = Response({"detail": "Session refreshed."}, status=status.HTTP_200_OK)
        return set_auth_cookies(response, access, refresh)


class LogoutView(APIView):
    # Allow logout even when access token is missing/expired.
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie_key = settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh")
        refresh = request.COOKIES.get(refresh_cookie_key)
        AuthService.logout_with_refresh_token(refresh_token=refresh)

        response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            AuthService.change_password(
                user=request.user,
                current_password=serializer.validated_data["current_password"],
                new_password=serializer.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        payload = {
            "id": user.id,
            "email": user.email,
            "is_email_verified": user.is_email_verified,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "date_joined": user.date_joined,
        }
        return Response(payload, status=status.HTTP_200_OK)


class AuthStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({"authenticated": False}, status=status.HTTP_200_OK)

        return Response(
            {
                "authenticated": True,
                "email": request.user.email,
                "is_email_verified": request.user.is_email_verified,
                "is_locked": request.user.is_locked,
            },
            status=status.HTTP_200_OK,
        )
