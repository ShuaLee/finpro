from django.core.management.base import BaseCommand

from profiles.services.bootstrap_service import ProfileBootstrapService
from users.models import User


class Command(BaseCommand):
    help = "Backfill missing profile/subscription/main portfolio for all users."

    def handle(self, *args, **options):
        total = 0
        for user in User.objects.all().iterator():
            ProfileBootstrapService.bootstrap(user=user)
            total += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete. Processed {total} user(s).",
            )
        )

