from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap schema master constraints, categories, and column catalog."

    def handle(self, *args, **options):
        call_command("seed_master_constraints")
        call_command("seed_schema_column_categories")
        call_command("seed_system_column_catalog")
        self.stdout.write(self.style.SUCCESS("Schemas bootstrap complete."))
