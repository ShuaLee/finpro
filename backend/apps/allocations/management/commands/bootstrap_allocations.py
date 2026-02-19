from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap allocations app (currently schema-only; no global seed data required)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Allocations bootstrap complete (no global seed data required)."))
