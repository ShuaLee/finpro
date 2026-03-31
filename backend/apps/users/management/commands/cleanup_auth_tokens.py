from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.users.models import (
    EmailVerificationToken,
    PasswordResetToken,
    TrustedDeviceToken,
)


class Command(BaseCommand):
    help = "Clean up expired, consumed, and revoked authentication tokens."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many tokens would be deleted without deleting them.",
        )
        parser.add_argument(
            "--retention-days",
            type=int,
            default=30,
            help="Retention period in days for consumed or revoked tokens.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        retention_days = options["retention_days"]
        now = timezone.now()
        retention_cutoff = now - timedelta(days=retention_days)

        email_tokens_qs = EmailVerificationToken.objects.filter(
            expires_at__lt=now,
        ) | EmailVerificationToken.objects.filter(
            consumed_at__isnull=False,
            consumed_at__lt=retention_cutoff,
        )

        password_tokens_qs = PasswordResetToken.objects.filter(
            expires_at__lt=now,
        ) | PasswordResetToken.objects.filter(
            consumed_at__isnull=False,
            consumed_at__lt=retention_cutoff,
        )

        trusted_device_tokens_qs = TrustedDeviceToken.objects.filter(
            expires_at__lt=now,
        ) | TrustedDeviceToken.objects.filter(
            revoked_at__isnull=False,
            revoked_at__lt=retention_cutoff,
        )

        email_count = email_tokens_qs.count()
        password_count = password_tokens_qs.count()
        trusted_count = trusted_device_tokens_qs.count()
        total_count = email_count + password_count + trusted_count

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run: no tokens deleted."
                )
            )
        else:
            email_tokens_qs.delete()
            password_tokens_qs.delete()
            trusted_device_tokens_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Email verification tokens: {email_count}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Password reset tokens: {password_count}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Trusted device tokens: {trusted_count}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Total auth tokens {'to delete' if dry_run else 'deleted'}: {total_count}"
            )
        )
