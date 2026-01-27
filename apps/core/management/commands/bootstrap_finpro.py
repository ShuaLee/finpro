from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = "🚀 Bootstrap the entire FinPro system (idempotent, ordered)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            "\n🚀 Starting FinPro bootstrap...\n"))

        steps = [
            # -------------------------------------------------
            # FX / Reference Data
            # -------------------------------------------------
            ("🌍 FX reference data (countries & currencies)", [
                "bootstrap_fx",
            ]),

            # -------------------------------------------------
            # Core system definitions
            # -------------------------------------------------
            ("📦 System AssetTypes", [
                "seed_asset_types",
            ]),

            # -------------------------------------------------
            # Account system
            # -------------------------------------------------
            ("🏦 Account system", [
                "seed_system_account_types",
            ]),

            # -------------------------------------------------
            # Formula + Schema system (MUST come before assets)
            # -------------------------------------------------
            ("🧮 Formula system", [
                "seed_formulas",
            ]),

            ("🧬 Schema system", [
                "seed_master_constraints",
                "seed_schema_column_categories",
                "seed_system_column_catalog",
            ]),

            # -------------------------------------------------
            # Asset universes
            # -------------------------------------------------
            ("🪙 Cryptocurrency universe", [
                "seed_cryptos",
            ]),

            ("📈 Equity universe", [
                "seed_equities",
            ]),

            ("🧱 Commodity universe", [
                "seed_commodities",
            ]),

            # -------------------------------------------------
            # Real estate reference data
            # -------------------------------------------------
            ("🏠 Real estate reference data", [
                "seed_real_estate_types",
            ]),
        ]

        for section_label, commands in steps:
            self.stdout.write(self.style.NOTICE(f"\n➡️  {section_label}"))

            for cmd in commands:
                self.stdout.write(f"   • Running `{cmd}`...")
                try:
                    with transaction.atomic():
                        call_command(cmd)
                except Exception as exc:
                    self.stdout.write(
                        self.style.ERROR(
                            f"\n❌ Bootstrap failed during `{cmd}`:\n{exc}"
                        )
                    )
                    raise  # fail fast, do NOT continue

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ FinPro bootstrap complete. System is ready.\n"
            )
        )
