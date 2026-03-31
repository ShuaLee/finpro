import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.users.models import TrustedDeviceToken


class TrustedDeviceService:
    COOKIE_NAME = getattr(settings, "AUTH_TRUSTED_DEVICE_COOKIE", "trusted_device")
    TRUST_DAYS = getattr(settings, "AUTH_TRUSTED_DEVICE_DAYS", 30)

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def issue_for_user(*, user):
        raw_token = secrets.token_urlsafe(48)
        token_hash = TrustedDeviceService._hash_token(raw_token)

        TrustedDeviceToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(days=TrustedDeviceService.TRUST_DAYS),
        )
        return raw_token

    @staticmethod
    def is_request_trusted_for_user(*, request, user) -> bool:
        raw_token = request.COOKIES.get(TrustedDeviceService.COOKIE_NAME)
        if not raw_token:
            return False

        token_hash = TrustedDeviceService._hash_token(raw_token)
        token = TrustedDeviceToken.objects.filter(
            user=user,
            token_hash=token_hash,
            revoked_at__isnull=True,
        ).first()
        if not token or token.is_expired:
            return False

        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
        return True

    @staticmethod
    def revoke_for_user(*, user, raw_token: str) -> bool:
        token_hash = TrustedDeviceService._hash_token(raw_token)
        updated = TrustedDeviceToken.objects.filter(
            user=user,
            token_hash=token_hash,
            revoked_at__isnull=True,
        ).update(revoked_at=timezone.now())
        return bool(updated)

