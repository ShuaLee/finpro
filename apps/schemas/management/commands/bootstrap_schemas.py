from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Bootstrap all schema-related system data (constraints, formulas, templates, etc.)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔧 Bootstrapping schema system..."))

        steps = [
            ("Seeding MasterConstraints", "seed_master_constraints"),
            ("Seeding Formulas", "seed_formulas"),
            ("Seeding Schema Templates", "seed_schema_template"),
            ("Resequencing SchemaColumns", "resequence_schema_columns"),
        ]

        for label, cmd in steps:
            self.stdout.write(f"\n➡️  {label}...")
            call_command(cmd)

        self.stdout.write(self.style.SUCCESS("\n✅ Schema bootstrap complete."))
