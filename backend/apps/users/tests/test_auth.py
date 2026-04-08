from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import EmailVerificationToken, SupportedCountry, SupportedCurrency


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        SupportedCurrency.objects.create(code="USD", name="US Dollar")
        SupportedCountry.objects.create(code="US", name="United States")

    def test_register_creates_user_profile_and_verification_token(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "test@example.com",
                "password": "StrongPass123!",
                "accept_terms": True,
                "full_name": "Test User",
                "language": "en",
                "timezone": "UTC",
                "country": "US",
                "currency": "USD",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = self.user_model.objects.get(email="test@example.com")
        self.assertEqual(user.profile.full_name, "Test User")
        self.assertEqual(user.profile.country, "US")
        self.assertEqual(user.profile.currency, "USD")
        self.assertTrue(
            EmailVerificationToken.objects.filter(
                user=user,
                purpose=EmailVerificationToken.Purpose.VERIFY_EMAIL,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_register_with_duplicate_email_returns_400(self):
        self.user_model.objects.create_user(
            email="test@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "test@example.com",
                "password": "StrongPass123!",
                "accept_terms": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Email is already registered.", str(response.data))

    def test_login_sets_auth_cookies_for_verified_user(self):
        user = self.user_model.objects.create_user(
            email="verified@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )

        response = self.client.post(
            reverse("auth-login"),
            {
                "email": user.email,
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

    def test_login_with_wrong_password_returns_400(self):
        user = self.user_model.objects.create_user(
            email="verified@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )

        response = self.client.post(
            reverse("auth-login"),
            {
                "email": user.email,
                "password": "WrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid credentials.", str(response.data))

    def test_verify_email_marks_user_verified(self):
        user = self.user_model.objects.create_user(
            email="verifyme@example.com",
            password="StrongPass123!",
        )
        from apps.users.services import EmailVerificationService

        code, _ = EmailVerificationService.issue_token(user=user)

        response = self.client.post(
            reverse("auth-email-verify"),
            {
                "email": user.email,
                "code": code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertIsNotNone(user.email_verified_at)

    def test_verify_email_with_invalid_code_returns_400(self):
        user = self.user_model.objects.create_user(
            email="verifyme@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("auth-email-verify"),
            {
                "email": user.email,
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid verification code.", str(response.data))

    def test_resend_verification_for_missing_user_returns_safe_200(self):
        response = self.client.post(
            reverse("auth-email-resend"),
            {
                "email": "missing@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("If the account exists", response.data["detail"])

    def test_password_reset_confirm_updates_password(self):
        user = self.user_model.objects.create_user(
            email="resetme@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        from apps.users.services import PasswordResetService

        raw_token, _ = PasswordResetService.issue_token(user=user)

        response = self.client.post(
            reverse("auth-password-reset-confirm"),
            {
                "token": raw_token,
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass123!"))

    def test_password_reset_request_for_missing_user_returns_safe_200(self):
        response = self.client.post(
            reverse("auth-password-reset-request"),
            {
                "email": "missing@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("If the account exists", response.data["detail"])

    def test_password_reset_confirm_with_invalid_token_returns_400(self):
        response = self.client.post(
            reverse("auth-password-reset-confirm"),
            {
                "token": "invalid-token",
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid password reset token.", str(response.data))

    def test_change_password_with_wrong_current_password_returns_400(self):
        user = self.user_model.objects.create_user(
            email="changepassword@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("auth-password-change"),
            {
                "current_password": "WrongPass123!",
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Current password is incorrect.", str(response.data))

    def test_email_change_request_with_wrong_password_returns_400(self):
        user = self.user_model.objects.create_user(
            email="emailchange@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("auth-email-change-request"),
            {
                "new_email": "updated@example.com",
                "current_password": "WrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Current password is incorrect.", str(response.data))

    def test_email_change_confirm_with_invalid_code_returns_400(self):
        user = self.user_model.objects.create_user(
            email="emailchange@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("auth-email-change-confirm"),
            {
                "new_email": "updated@example.com",
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid verification code.", str(response.data))
