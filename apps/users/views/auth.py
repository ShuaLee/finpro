from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers.auth import (
    RegisterSerializer,
    LoginSerializer,
    VerifyEmailSerializer,
    ResendVerificationSerializer,
)
from users.services import AuthService, EmailVerificationService
from users.cookie import set_auth_cookies, clear_auth_cookies


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
            {"detail": "Registration successful. Check your email for verification.", "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = EmailVerificationService.verify_raw_token(raw_token=serializer.validated_data["token"])
        except DjangoValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Email verified.", "email": user.email}, status=status.HTTP_200_OK)


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        from users.models import User
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"detail": "If this email exists, a verification email was sent."}, status=status.HTTP_200_OK)

        try:
            EmailVerificationService.resend_for_user(user=user)
        except DjangoValidationError:
            pass

        return Response({"detail": "If this email exists, a verification email was sent."}, status=status.HTTP_200_OK)


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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.COOKIES.get("refresh")
        AuthService.logout_with_refresh_token(refresh_token=refresh)

        response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response
