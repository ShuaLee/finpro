from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import EmailVerificationToken, PasswordResetToken


class Command(BaseCommand):
    help = "Delete expired/consumed user verification and password reset tokens"

    def handle(self, *args, **options):
        now = timezone.now()

        deleted_verify = EmailVerificationToken.objects.filter(
            consumed_at__isnull=False,
        ).delete()[0]
        deleted_verify += EmailVerificationToken.objects.filter(
            expires_at__lt=now,
        ).delete()[0]

        deleted_reset = PasswordResetToken.objects.filter(
            consumed_at__isnull=False,
        ).delete()[0]
        deleted_reset += PasswordResetToken.objects.filter(
            expires_at__lt=now,
        ).delete()[0]

        self.stdout.write(
            self.style.SUCCESS(
                "Cleanup complete. "
                f"EmailVerificationToken deleted={deleted_verify}, "
                f"PasswordResetToken deleted={deleted_reset}"
            )
        )
