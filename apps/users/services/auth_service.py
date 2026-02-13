from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.services.email_verification_service import EmailVerificationService
from profiles.services.bootstrap_service import ProfileBootstrapService


class AuthService:
    @staticmethod
    @transaction.atomic
    def register_user(*, email: str, password: str, accept_terms: bool):
        if not accept_terms:
            raise ValidationError("You must accept terms to register.")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email is already registered.")

        user = User.objects.create_user(email=email, password=password)

        # Ensure foundational user context exists immediately
        ProfileBootstrapService.bootstrap(user=user)

        raw, _ = EmailVerificationService.issue_token(user=user)
        EmailVerificationService.send_verification_email(user=user, raw_token=raw)

        return user

    @staticmethod
    def login_user(*, email: str, password: str):
        user = authenticate(username=email, password=password)
        if not user:
            raise ValidationError("Invalid credentials.")

        if user.is_locked:
            raise ValidationError("Account is temporarily locked.")

        if not user.is_email_verified:
            raise ValidationError("Please verify your email first.")

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return user, access, refresh

    @staticmethod
    def logout_with_refresh_token(*, refresh_token: str | None):
        if not refresh_token:
            return
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return
