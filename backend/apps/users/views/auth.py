from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.cookie import clear_auth_cookies, set_auth_cookies
from users.serializers.auth import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
)
from users.services import AuthService, EmailVerificationService, PasswordResetService


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
                "detail": "Registration successful. Check your email for verification.",
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
            user = EmailVerificationService.verify_raw_token(
                raw_token=serializer.validated_data["token"]
            )
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Email verified.", "email": user.email}, status=status.HTTP_200_OK)


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
            user, access, refresh = AuthService.login_user(**serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response(
            {"detail": "Login successful.", "email": user.email},
            status=status.HTTP_200_OK,
        )
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
