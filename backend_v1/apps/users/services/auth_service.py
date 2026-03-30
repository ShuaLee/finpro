import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import EmailVerificationToken, User
from users.services.email_verification_service import EmailVerificationService
from profiles.services.bootstrap_service import ProfileBootstrapService


class AuthService:
    MAX_FAILED_LOGIN_ATTEMPTS = getattr(settings, "AUTH_MAX_FAILED_LOGIN_ATTEMPTS", 5)
    LOCKOUT_MINUTES = getattr(settings, "AUTH_LOCKOUT_MINUTES", 15)
    REQUIRE_EMAIL_VERIFICATION = getattr(settings, "AUTH_REQUIRE_EMAIL_VERIFICATION", True)
    EMAIL_CHANGE_CODE_TTL_MINUTES = getattr(settings, "AUTH_EMAIL_VERIFICATION_TTL_MINUTES", 10)
    EMAIL_CHANGE_COOLDOWN_SECONDS = getattr(settings, "AUTH_RESEND_VERIFICATION_COOLDOWN_SECONDS", 60)
    EMAIL_CHANGE_CODE_LENGTH = 6

    @staticmethod
    def _hash_code(*, salt: str, code: str) -> str:
        digest = hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()
        return f"{salt}${digest}"

    @staticmethod
    def _is_code_match(*, code: str, stored_hash: str) -> bool:
        salt, _, digest = stored_hash.partition("$")
        if not salt or not digest:
            return False
        expected = hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()
        return secrets.compare_digest(digest, expected)

    @staticmethod
    def _generate_code() -> str:
        return f"{secrets.randbelow(10 ** AuthService.EMAIL_CHANGE_CODE_LENGTH):0{AuthService.EMAIL_CHANGE_CODE_LENGTH}d}"

    @staticmethod
    def _latest_email_change_target(*, user) -> str | None:
        token = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
            target_email__isnull=False,
        ).order_by("-created_at").first()
        return token.target_email if token else None

    @staticmethod
    @transaction.atomic
    def _issue_email_change_token(*, user, target_email: str):
        cutoff = timezone.now() - timedelta(seconds=AuthService.EMAIL_CHANGE_COOLDOWN_SECONDS)
        recent = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
            created_at__gte=cutoff,
        ).exists()
        if recent:
            raise ValidationError("Please wait before requesting another email verification code.")

        EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())

        code = AuthService._generate_code()
        salt = secrets.token_hex(8)
        token_hash = AuthService._hash_code(salt=salt, code=code)

        EmailVerificationToken.objects.create(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            token_hash=token_hash,
            target_email=target_email,
            expires_at=timezone.now() + timedelta(minutes=AuthService.EMAIL_CHANGE_CODE_TTL_MINUTES),
        )

        subject = "Confirm your new FinPro email"
        message = (
            "Use this 6-digit code to confirm your new FinPro login email:\n\n"
            f"{code}\n\n"
            f"This code expires in {AuthService.EMAIL_CHANGE_CODE_TTL_MINUTES} minutes."
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@finpro.local"),
            recipient_list=[target_email],
            fail_silently=False,
        )
        return target_email

    @staticmethod
    @transaction.atomic
    def register_user(*, email: str, password: str, accept_terms: bool, full_name: str = ""):
        if not accept_terms:
            raise ValidationError("You must accept terms to register.")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email is already registered.")

        user = User.objects.create_user(email=email, password=password)

        # Ensure foundational user context exists immediately
        profile = ProfileBootstrapService.bootstrap(user=user)

        cleaned_full_name = (full_name or "").strip()
        if cleaned_full_name:
            profile.full_name = cleaned_full_name
            profile.save(update_fields=["full_name", "updated_at"])

        code, _ = EmailVerificationService.issue_token(user=user)
        EmailVerificationService.send_verification_email(user=user, verification_code=code)

        return user

    @staticmethod
    def login_user(*, email: str, password: str):
        user = AuthService.authenticate_user(email=email, password=password)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return user, access, refresh

    @staticmethod
    def authenticate_user(*, email: str, password: str):
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

        return user

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

    @staticmethod
    @transaction.atomic
    def get_pending_email_change(*, user) -> str | None:
        return AuthService._latest_email_change_target(user=user)

    @staticmethod
    @transaction.atomic
    def request_email_change(*, user, new_email: str, current_password: str):
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")

        normalized_email = (new_email or "").strip().lower()
        if not normalized_email:
            raise ValidationError("Email is required.")

        if user.email.lower() == normalized_email:
            return user

        if User.objects.filter(email__iexact=normalized_email).exclude(pk=user.pk).exists():
            raise ValidationError("Email is already registered.")

        return AuthService._issue_email_change_token(user=user, target_email=normalized_email)

    @staticmethod
    @transaction.atomic
    def resend_email_change_code(*, user):
        target_email = AuthService._latest_email_change_target(user=user)
        if not target_email:
            raise ValidationError("No pending email change to resend.")
        return AuthService._issue_email_change_token(user=user, target_email=target_email)

    @staticmethod
    @transaction.atomic
    def cancel_email_change(*, user):
        updated = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())
        if not updated:
            raise ValidationError("No pending email change to cancel.")
        return True

    @staticmethod
    @transaction.atomic
    def confirm_email_change(*, user, new_email: str, code: str):
        normalized_email = (new_email or "").strip().lower()
        if not normalized_email:
            raise ValidationError("Email is required.")

        if User.objects.filter(email__iexact=normalized_email).exclude(pk=user.pk).exists():
            raise ValidationError("Email is already registered.")

        active_tokens = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
            target_email__iexact=normalized_email,
        ).order_by("-created_at")

        matched = None
        for candidate in active_tokens:
            if candidate.is_expired:
                continue
            if AuthService._is_code_match(code=code, stored_hash=candidate.token_hash):
                matched = candidate
                break

        if matched is None:
            raise ValidationError("Invalid verification code.")

        now = timezone.now()
        user.email = normalized_email
        user.email_verified_at = now
        user.save(update_fields=["email", "email_verified_at"])

        matched.consumed_at = now
        matched.save(update_fields=["consumed_at"])

        EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
        ).update(consumed_at=now)
        return user

