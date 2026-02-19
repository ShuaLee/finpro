from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap formulas and formula definitions."

    def handle(self, *args, **options):
        call_command("seed_formulas")
        self.stdout.write(self.style.SUCCESS("Formulas bootstrap complete."))
