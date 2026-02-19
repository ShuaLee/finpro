from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from users.services.email_verification_service import EmailVerificationService
from profiles.services.bootstrap_service import ProfileBootstrapService


class AuthService:
    MAX_FAILED_LOGIN_ATTEMPTS = getattr(settings, "AUTH_MAX_FAILED_LOGIN_ATTEMPTS", 5)
    LOCKOUT_MINUTES = getattr(settings, "AUTH_LOCKOUT_MINUTES", 15)
    REQUIRE_EMAIL_VERIFICATION = getattr(settings, "AUTH_REQUIRE_EMAIL_VERIFICATION", True)

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
        normalized_email = (email or "").strip().lower()
        user = User.objects.filter(email__iexact=normalized_email).first()

        if not user:
            raise ValidationError("Invalid credentials.")

        if user.is_locked:
            raise ValidationError("Account is temporarily locked.")

        if not user.check_password(password):
            user.failed_login_count += 1
            update_fields = ["failed_login_count"]

            if user.failed_login_count >= AuthService.MAX_FAILED_LOGIN_ATTEMPTS:
                user.failed_login_count = 0
                user.locked_until = timezone.now() + timedelta(minutes=AuthService.LOCKOUT_MINUTES)
                update_fields.append("locked_until")

            user.save(update_fields=update_fields)
            raise ValidationError("Invalid credentials.")

        if not user.is_active:
            raise ValidationError("Invalid credentials.")

        if AuthService.REQUIRE_EMAIL_VERIFICATION and not user.is_email_verified:
            raise ValidationError("Please verify your email first.")

        if user.failed_login_count != 0 or user.locked_until is not None:
            user.failed_login_count = 0
            user.locked_until = None
            user.save(update_fields=["failed_login_count", "locked_until"])

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

    @staticmethod
    def change_password(*, user, current_password: str, new_password: str):
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")

        from django.contrib.auth.password_validation import validate_password

        validate_password(new_password, user=user)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        return user

