from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap account system reference data."

    def handle(self, *args, **options):
        call_command("seed_system_account_types")
        self.stdout.write(self.style.SUCCESS("Accounts bootstrap complete."))
