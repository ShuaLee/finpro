from datetime import timedelta
from typing import Any, cast

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import AuthEvent, EmailVerificationToken, User
from apps.users.services.auth_event_service import AuthEventService
from apps.users.services.email_verification_service import EmailVerificationService
from apps.users.services.profile_creation_service import ProfileCreationService
from apps.users.services.trusted_device_service import TrustedDeviceService
from apps.users.services.user_creation_service import UserCreationService


class AuthService:
    MAX_FAILED_LOGIN_ATTEMPTS = getattr(
        settings, "AUTH_MAX_FAILED_LOGIN_ATTEMPTS", 5)
    LOCKOUT_MINUTES = getattr(settings, "AUTH_LOCKOUT_MINUTES", 15)
    REQUIRE_EMAIL_VERIFICATION = getattr(
        settings, "AUTH_REQUIRE_EMAIL_VERIFICATION", True)
    EMAIL_CHANGE_CODE_TTL_MINUTES = getattr(
        settings, "AUTH_EMAIL_VERIFICATION_TTL_MINUTES", 10)
    EMAIL_CHANGE_COOLDOWN_SECONDS = getattr(
        settings, "AUTH_RESEND_VERIFICATION_COOLDOWN_SECONDS", 60)

    @staticmethod
    def _client_ip(*, request) -> str | None:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def _user_agent(*, request) -> str:
        return request.META.get("HTTP_USER_AGENT", "")

    @staticmethod
    @transaction.atomic
    def register_user(
        *,
        email: str,
        password: str,
        accept_terms: bool,
        full_name: str = "",
        language: str = "en",
        timezone_name: str = "UTC",
        currency: str = "USD",
        request=None,
    ):
        if not accept_terms:
            raise ValidationError("You must accept terms to register.")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email is already registered.")

        user = UserCreationService.create_user(
            email=email,
            password=password,
            full_name=full_name,
            language=language,
            timezone=timezone_name,
            currency=currency,
        )

        code, _ = EmailVerificationService.issue_token(user=user)
        EmailVerificationService.send_verification_email(
            user=user,
            verification_code=code,
        )

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.REGISTERED,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )
        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.EMAIL_VERIFICATION_SENT,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )

        return user

    @staticmethod
    def authenticate_user(*, email: str, password: str, request=None):
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

                AuthEventService.log_event(
                    user=user,
                    event_type=AuthEvent.EventType.ACCOUNT_LOCKED,
                    ip_address=AuthService._client_ip(
                        request=request) if request else None,
                    user_agent=AuthService._user_agent(
                        request=request) if request else "",
                )

            user.save(update_fields=update_fields)

            AuthEventService.log_event(
                user=user,
                event_type=AuthEvent.EventType.LOGIN_FAILED,
                ip_address=AuthService._client_ip(
                    request=request) if request else None,
                user_agent=AuthService._user_agent(
                    request=request) if request else "",
            )
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
    def login_user(*, email: str, password: str, request=None):
        user = AuthService.authenticate_user(
            email=email,
            password=password,
            request=request,
        )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.LOGIN_SUCCEEDED,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )

        return user, access, refresh

    @staticmethod
    def logout_with_refresh_token(*, user, refresh_token: str | None, request=None):
        if refresh_token:
            try:
                token = RefreshToken(cast(Any, refresh_token))
                token.blacklist()
            except Exception:
                pass

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.LOGOUT,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )
        return True

    @staticmethod
    def change_password(*, user, current_password: str, new_password: str, request=None):
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")

        validate_password(new_password, user=user)

        user.set_password(new_password)
        user.save(update_fields=["password"])

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.PASSWORD_CHANGED,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )

        return user

    @staticmethod
    def resend_verification_for_user(*, user, request=None):
        if user.is_email_verified:
            raise ValidationError("Email already verified.")

        code, _ = EmailVerificationService.issue_token(user=user)
        EmailVerificationService.send_verification_email(
            user=user,
            verification_code=code,
        )

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.EMAIL_VERIFICATION_SENT,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )
        return True

    @staticmethod
    def verify_email_code(*, email: str, code: str, request=None):
        user = EmailVerificationService.verify_email_code(
            email=email, code=code)

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.EMAIL_VERIFIED,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
        )
        return user

    @staticmethod
    def request_email_change(*, user, new_email: str, current_password: str, request=None):
        if not user.check_password(current_password):
            raise ValidationError("Current password is incorrect.")

        normalized_email = (new_email or "").strip().lower()
        if not normalized_email:
            raise ValidationError("Email is required.")

        if user.email.lower() == normalized_email:
            return user

        if User.objects.filter(email__iexact=normalized_email).exclude(pk=user.pk).exists():
            raise ValidationError("Email is already registered.")

        cutoff = timezone.now() - timedelta(seconds=AuthService.EMAIL_CHANGE_COOLDOWN_SECONDS)
        recent = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
            created_at__gte=cutoff,
        ).exists()
        if recent:
            raise ValidationError(
                "Please wait before requesting another email verification code.")

        EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.EMAIL_CHANGE,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())

        code, token = EmailVerificationService.issue_token(user=user)
        token.purpose = EmailVerificationToken.Purpose.EMAIL_CHANGE
        token.target_email = normalized_email
        token.save(update_fields=["purpose", "target_email"])

        EmailVerificationService.send_verification_email(
            user=user,
            verification_code=code,
        )

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.EMAIL_CHANGE_REQUESTED,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
            metadata={"target_email": normalized_email},
        )

        return normalized_email

    @staticmethod
    def confirm_email_change(*, user, new_email: str, code: str, request=None):
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
            if EmailVerificationService._is_code_match(
                code=code,
                stored_hash=candidate.token_hash,
            ):
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

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.EMAIL_CHANGED,
            ip_address=AuthService._client_ip(
                request=request) if request else None,
            user_agent=AuthService._user_agent(
                request=request) if request else "",
            metadata={"new_email": normalized_email},
        )

        return user

    @staticmethod
    def trust_current_device(*, user, request):
        raw_token = TrustedDeviceService.issue_for_user(user=user)

        AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.TRUSTED_DEVICE_ADDED,
            ip_address=AuthService._client_ip(request=request),
            user_agent=AuthService._user_agent(request=request),
        )

        return raw_token

    @staticmethod
    def revoke_trusted_device(*, user, raw_token: str, request=None):
        revoked = TrustedDeviceService.revoke_for_user(
            user=user, raw_token=raw_token)
        if revoked:
            AuthEventService.log_event(
                user=user,
                event_type=AuthEvent.EventType.TRUSTED_DEVICE_REVOKED,
                ip_address=AuthService._client_ip(
                    request=request) if request else None,
                user_agent=AuthService._user_agent(
                    request=request) if request else "",
            )
        return revoked

    @staticmethod
    def update_profile(
        *,
        user,
        full_name: str = "",
        language: str = "en",
        timezone_name: str = "UTC",
        currency: str = "USD",
    ):
        return ProfileCreationService.update_profile(
            user=user,
            full_name=full_name,
            language=language,
            timezone=timezone_name,
            currency=currency,
        )
