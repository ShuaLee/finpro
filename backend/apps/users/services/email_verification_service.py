import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from users.models import EmailVerificationToken


class EmailVerificationService:
    CODE_TTL_MINUTES = getattr(settings, "AUTH_EMAIL_VERIFICATION_TTL_MINUTES", 10)
    CODE_LENGTH = 6
    RESEND_COOLDOWN_SECONDS = getattr(
        settings, "AUTH_RESEND_VERIFICATION_COOLDOWN_SECONDS", 60
    )

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
        return f"{secrets.randbelow(10 ** EmailVerificationService.CODE_LENGTH):0{EmailVerificationService.CODE_LENGTH}d}"

    @staticmethod
    def issue_token(*, user):
        cutoff = timezone.now() - timedelta(
            seconds=EmailVerificationService.RESEND_COOLDOWN_SECONDS
        )

        recent = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            consumed_at__isnull=True,
            created_at__gte=cutoff,
        ).exists()
        if recent:
            raise ValidationError(
                "Please wait before requesting another verification email."
            )

        EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())

        code = EmailVerificationService._generate_code()
        salt = secrets.token_hex(8)
        token_hash = EmailVerificationService._hash_code(salt=salt, code=code)

        token = EmailVerificationToken.objects.create(
            user=user,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(minutes=EmailVerificationService.CODE_TTL_MINUTES),
        )
        return code, token

    @staticmethod
    def send_verification_email(*, user, verification_code: str):
        subject = "Your FinPro verification code"
        message = (
            "Use this 6-digit code to verify your FinPro account:\n\n"
            f"{verification_code}\n\n"
            f"This code expires in {EmailVerificationService.CODE_TTL_MINUTES} minutes."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@finpro.local"),
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def verify_email_code(*, email: str, code: str):
        normalized_email = (email or "").strip().lower()

        from users.models import User

        user = User.objects.filter(email__iexact=normalized_email).first()
        if not user:
            raise ValidationError("Invalid verification code.")

        active_tokens = EmailVerificationToken.objects.select_related("user").filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            consumed_at__isnull=True,
        ).order_by("-created_at")

        token = None
        for candidate in active_tokens:
            if candidate.is_expired:
                continue
            if EmailVerificationService._is_code_match(
                code=code,
                stored_hash=candidate.token_hash,
            ):
                token = candidate
                break

        if token is None:
            raise ValidationError("Invalid verification code.")

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

        code, _ = EmailVerificationService.issue_token(user=user)
        EmailVerificationService.send_verification_email(user=user, verification_code=code)
        return True
