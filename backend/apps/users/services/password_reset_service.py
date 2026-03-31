import hashlib
import secrets
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from apps.users.models import PasswordResetToken


class PasswordResetService:
    TOKEN_TTL_HOURS = getattr(settings, "AUTH_PASSWORD_RESET_TTL_HOURS", 1)
    TOKEN_BYTES = getattr(settings, "AUTH_PASSWORD_RESET_TOKEN_BYTES", 32)
    RESEND_COOLDOWN_SECONDS = getattr(
        settings,
        "AUTH_PASSWORD_RESET_COOLDOWN_SECONDS",
        60,
    )

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_token(raw_token: str) -> str:
        token = (raw_token or "").strip().replace("\r", "").replace("\n", "")
        token = token.replace("=3D", "=").replace("=3d", "=")

        if token.startswith("3D"):
            token = token[2:]

        token = token.replace("=", "")
        return token

    @staticmethod
    def issue_token(*, user):
        cutoff = timezone.now() - timedelta(
            seconds=PasswordResetService.RESEND_COOLDOWN_SECONDS
        )

        recent = PasswordResetToken.objects.filter(
            user=user,
            consumed_at__isnull=True,
            created_at__gte=cutoff,
        ).exists()
        if recent:
            raise ValidationError(
                "Please wait before requesting another reset email."
            )

        PasswordResetToken.objects.filter(
            user=user,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())

        raw = secrets.token_urlsafe(PasswordResetService.TOKEN_BYTES)
        token_hash = PasswordResetService._hash_token(raw)

        token = PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now()
            + timedelta(hours=PasswordResetService.TOKEN_TTL_HOURS),
        )
        return raw, token

    @staticmethod
    def send_reset_email(*, user, raw_token: str):
        frontend_base = getattr(settings, "FRONTEND_URL",
                                "http://localhost:5173")
        reset_url = f"{frontend_base}/reset-password?token={quote(raw_token, safe='')}"

        subject = "Reset your password"
        message = (
            "Click to reset your password:\n\n"
            f"{reset_url}\n\n"
            "This link expires soon."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                "no-reply@finpro.local",
            ),
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def request_for_email(*, user):
        raw, _ = PasswordResetService.issue_token(user=user)
        PasswordResetService.send_reset_email(user=user, raw_token=raw)
        return True

    @staticmethod
    def reset_with_token(*, raw_token: str, new_password: str):
        normalized_token = PasswordResetService._normalize_token(raw_token)
        if not normalized_token:
            raise ValidationError("Invalid password reset token.")

        token_hash = PasswordResetService._hash_token(normalized_token)
        token = PasswordResetToken.objects.select_related("user").filter(
            token_hash=token_hash
        ).first()

        if not token:
            raise ValidationError("Invalid password reset token.")

        if token.is_consumed:
            raise ValidationError("Password reset token already used.")

        if token.is_expired:
            raise ValidationError("Password reset token expired.")

        user = token.user
        validate_password(new_password, user=user)

        user.set_password(new_password)
        user.failed_login_count = 0
        user.locked_until = None
        user.save(update_fields=["password",
                  "failed_login_count", "locked_until"])

        token.consumed_at = timezone.now()
        token.save(update_fields=["consumed_at"])

        return user
