import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from users.models import EmailVerificationToken, User


class LoginSecurityCodeService:
    CODE_LENGTH = 6
    CODE_TTL_MINUTES = getattr(settings, "AUTH_LOGIN_CODE_TTL_MINUTES", 10)
    RESEND_COOLDOWN_SECONDS = getattr(settings, "AUTH_LOGIN_CODE_COOLDOWN_SECONDS", 60)

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
        return f"{secrets.randbelow(10 ** LoginSecurityCodeService.CODE_LENGTH):0{LoginSecurityCodeService.CODE_LENGTH}d}"

    @staticmethod
    def issue_for_user(*, user):
        cutoff = timezone.now() - timedelta(seconds=LoginSecurityCodeService.RESEND_COOLDOWN_SECONDS)

        recent = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.LOGIN_SECURITY,
            consumed_at__isnull=True,
            created_at__gte=cutoff,
        ).exists()
        if recent:
            raise ValidationError("Please wait before requesting another security code.")

        EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.LOGIN_SECURITY,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())

        code = LoginSecurityCodeService._generate_code()
        salt = secrets.token_hex(8)
        token_hash = LoginSecurityCodeService._hash_code(salt=salt, code=code)

        token = EmailVerificationToken.objects.create(
            user=user,
            purpose=EmailVerificationToken.Purpose.LOGIN_SECURITY,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(minutes=LoginSecurityCodeService.CODE_TTL_MINUTES),
        )
        return code, token

    @staticmethod
    def send_code_email(*, user, code: str):
        subject = "Your FinPro security code"
        message = (
            "Use this 6-digit code to complete your sign in:\n\n"
            f"{code}\n\n"
            f"This code expires in {LoginSecurityCodeService.CODE_TTL_MINUTES} minutes."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@finpro.local"),
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def issue_and_send(*, user):
        code, _ = LoginSecurityCodeService.issue_for_user(user=user)
        LoginSecurityCodeService.send_code_email(user=user, code=code)

    @staticmethod
    def verify_code(*, email: str, code: str):
        normalized_email = (email or "").strip().lower()
        user = User.objects.filter(email__iexact=normalized_email).first()
        if not user:
            raise ValidationError("Invalid security code.")

        active_tokens = EmailVerificationToken.objects.filter(
            user=user,
            purpose=EmailVerificationToken.Purpose.LOGIN_SECURITY,
            consumed_at__isnull=True,
        ).order_by("-created_at")

        token = None
        for candidate in active_tokens:
            if candidate.is_expired:
                continue
            if LoginSecurityCodeService._is_code_match(code=code, stored_hash=candidate.token_hash):
                token = candidate
                break

        if token is None:
            raise ValidationError("Invalid security code.")

        token.consumed_at = timezone.now()
        token.save(update_fields=["consumed_at"])
        return user
