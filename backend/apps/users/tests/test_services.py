from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.users.models import AuthEvent, TrustedDeviceToken
from apps.users.services import (
    AuthEventService,
    EmailVerificationService,
    PasswordResetService,
    TrustedDeviceService,
    UserCreationService,
)


class UserServiceTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_user_creation_service_creates_user_and_profile(self):
        user = UserCreationService.create_user(
            email="service@example.com",
            password="StrongPass123!",
            full_name="Service User",
            language="en",
            timezone="UTC",
            currency="USD",
        )

        self.assertEqual(user.email, "service@example.com")
        self.assertEqual(user.profile.full_name, "Service User")
        self.assertEqual(user.profile.currency, "USD")

    def test_email_verification_service_issues_and_verifies_code(self):
        user = self.user_model.objects.create_user(
            email="verify@example.com",
            password="StrongPass123!",
        )

        code, token = EmailVerificationService.issue_token(user=user)

        self.assertEqual(token.user, user)
        verified_user = EmailVerificationService.verify_email_code(
            email=user.email,
            code=code,
        )

        self.assertEqual(verified_user.pk, user.pk)
        user.refresh_from_db()
        self.assertIsNotNone(user.email_verified_at)

    def test_password_reset_service_resets_password(self):
        user = self.user_model.objects.create_user(
            email="password@example.com",
            password="StrongPass123!",
        )

        raw_token, _ = PasswordResetService.issue_token(user=user)
        PasswordResetService.reset_with_token(
            raw_token=raw_token,
            new_password="UpdatedStrongPass123!",
        )

        user.refresh_from_db()
        self.assertTrue(user.check_password("UpdatedStrongPass123!"))

    def test_trusted_device_service_issue_and_revoke(self):
        user = self.user_model.objects.create_user(
            email="trusted@example.com",
            password="StrongPass123!",
        )

        raw_token = TrustedDeviceService.issue_for_user(user=user)
        self.assertTrue(
            TrustedDeviceToken.objects.filter(user=user).exists()
        )

        revoked = TrustedDeviceService.revoke_for_user(user=user, raw_token=raw_token)
        self.assertTrue(revoked)
        self.assertTrue(
            TrustedDeviceToken.objects.filter(user=user, revoked_at__isnull=False).exists()
        )

    def test_auth_event_service_logs_event(self):
        user = self.user_model.objects.create_user(
            email="event@example.com",
            password="StrongPass123!",
        )
        request = RequestFactory().get("/", HTTP_USER_AGENT="pytest-agent")

        event = AuthEventService.log_event(
            user=user,
            event_type=AuthEvent.EventType.LOGIN_SUCCEEDED,
            ip_address="127.0.0.1",
            user_agent=request.META["HTTP_USER_AGENT"],
            metadata={"source": "test"},
        )

        self.assertEqual(event.user, user)
        self.assertEqual(event.metadata["source"], "test")

