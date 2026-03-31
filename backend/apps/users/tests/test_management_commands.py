from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.users.models import (
    EmailVerificationToken,
    PasswordResetToken,
    TrustedDeviceToken,
)


class UserManagementCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="command@example.com",
            password="StrongPass123!",
        )

    def test_cleanup_auth_tokens_removes_expired_tokens(self):
        now = timezone.now()

        EmailVerificationToken.objects.create(
            user=self.user,
            purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            token_hash="expired-email-token",
            expires_at=now - timedelta(days=1),
        )
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash="expired-password-token",
            expires_at=now - timedelta(days=1),
        )
        TrustedDeviceToken.objects.create(
            user=self.user,
            token_hash="expired-trusted-token",
            expires_at=now - timedelta(days=1),
        )

        call_command("cleanup_auth_tokens")

        self.assertEqual(EmailVerificationToken.objects.count(), 0)
        self.assertEqual(PasswordResetToken.objects.count(), 0)
        self.assertEqual(TrustedDeviceToken.objects.count(), 0)
