from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models.account_type import AccountType
from accounts.models.account_classification import ClassificationDefinition
from assets.models.core import AssetType
from fx.models.country import Country


class Command(BaseCommand):
    help = "Seed system AccountTypes and ClassificationDefinitions"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding system AccountTypes...")

        # -------------------------------------------------
        # AssetType lookup (MATCHES EXISTING SYSTEM TYPES)
        # -------------------------------------------------
        asset_types = {
            "equity": AssetType.objects.get(slug="equity"),
            "cryptocurrency": AssetType.objects.get(slug="cryptocurrency"),
            "real_estate": AssetType.objects.get(slug="real-estate"),
        }

        account_types = [
            {
                "name": "Brokerage",
                "slug": "brokerage",
                "asset_types": ["equity"],
            },
            {
                "name": "Cryptocurrency Wallet",
                "slug": "crypto-wallet",
                "asset_types": ["cryptocurrency"],
            },
            {
                "name": "Real Estate",
                "slug": "real-estate",
                "asset_types": ["real_estate"],
            },
        ]

        for data in account_types:
            obj, created = AccountType.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "is_system": True,
                },
            )

            if created:
                obj.allowed_asset_types.set(
                    [asset_types[key] for key in data["asset_types"]]
                )
                self.stdout.write(f"  ✅ Created AccountType: {obj.name}")
            else:
                self.stdout.write(f"  ↪ Skipped (exists): {obj.name}")

        # -------------------------------------------------
        # Classification Definitions
        # -------------------------------------------------
        self.stdout.write("🌱 Seeding ClassificationDefinitions...")

        canada = Country.objects.get(code="CA")

        classifications = [
            {
                "name": "General",
                "tax_status": "taxable",
                "all_countries": True,
                "countries": [],
            },
            {
                "name": "Tax-Free Savings Account (TFSA)",
                "tax_status": "tax_exempt",
                "all_countries": False,
                "countries": [canada],
            },
        ]

        for data in classifications:
            obj, created = ClassificationDefinition.objects.get_or_create(
                name=data["name"],
                defaults={
                    "tax_status": data["tax_status"],
                    "all_countries": data["all_countries"],
                    "is_system": True,
                },
            )

            if not obj.all_countries:
                obj.countries.set(data["countries"])

            if created:
                self.stdout.write(f"  ✅ Created Classification: {obj.name}")
            else:
                self.stdout.write(f"  ↪ Skipped (exists): {obj.name}")

        self.stdout.write(
            self.style.SUCCESS(
                "✅ System AccountTypes and Classifications seeded")
        )
