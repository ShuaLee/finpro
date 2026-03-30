from django.core.management.base import BaseCommand
from django.db import transaction

from subscriptions.signals import create_default_plans


class Command(BaseCommand):
    help = "Bootstrap subscription plans and entitlements."

    @transaction.atomic
    def handle(self, *args, **options):
        create_default_plans(sender=None)
        self.stdout.write(self.style.SUCCESS("Subscriptions bootstrap complete."))
