import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from users.models import EmailVerificationToken


class EmailVerificationService:
    TOKEN_TTL_HOURS = 24

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def issue_token(*, user):
        raw = secrets.token_urlsafe(48)
        token_hash = EmailVerificationService._hash_token(raw)

        token = EmailVerificationToken.objects.create(
            user=user,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=EmailVerificationService.TOKEN_TTL_HOURS),
        )
        return raw, token

    @staticmethod
    def send_verification_email(*, user, raw_token: str):
        frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        verify_url = f"{frontend_base}/verify-email?token={raw_token}"

        subject = "Verify your email"
        message = (
            "Click to verify your email:\n\n"
            f"{verify_url}\n\n"
            "This link expires in 24 hours."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@finpro.local"),
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def verify_raw_token(*, raw_token: str):
        token_hash = EmailVerificationService._hash_token(raw_token)
        token = EmailVerificationToken.objects.select_related("user").filter(
            token_hash=token_hash,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
        ).first()

        if not token:
            raise ValidationError("Invalid verification token.")

        if token.is_consumed:
            raise ValidationError("Verification token already used.")

        if token.is_expired:
            raise ValidationError("Verification token expired.")

        user = token.user
        now = timezone.now()

        if user.email_verified_at is None:
            user.email_verified_at = now
            user.save(update_fields=["email_verified_at"])

        token.consumed_at = now
        token.save(update_fields=["consumed_at"])

        return user

    @staticmethod
    def resend_for_user(*, user):
        if user.is_email_verified:
            raise ValidationError("Email already verified.")

        raw, _ = EmailVerificationService.issue_token(user=user)
        EmailVerificationService.send_verification_email(user=user, raw_token=raw)
        return True
