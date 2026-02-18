from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models.account_type import AccountType
from accounts.models.account_classification import ClassificationDefinition
from assets.models.core import AssetType
from fx.models.country import Country


class Command(BaseCommand):
    help = "Seed system AccountTypes and ClassificationDefinitions"

    @staticmethod
    def _get_asset_type(*slugs):
        found = AssetType.objects.filter(slug__in=slugs).first()
        if not found:
            raise AssetType.DoesNotExist(
                f"AssetType not found for any of: {', '.join(slugs)}"
            )
        return found

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding system AccountTypes...")

        asset_types = {
            "equity": self._get_asset_type("equity"),
            "crypto": self._get_asset_type("crypto", "cryptocurrency"),
            "real_estate": self._get_asset_type("real_estate", "real-estate"),
            "commodity": self._get_asset_type("commodity"),
            "precious_metal": self._get_asset_type("precious_metal", "precious-metal"),
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
                "asset_types": ["crypto"],
            },
            {
                "name": "Real Estate",
                "slug": "real-estate",
                "asset_types": ["real_estate"],
            },
            {
                "name": "Precious Metal",
                "slug": "precious-metal",
                "asset_types": ["precious_metal"],
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

            desired_assets = [asset_types[key] for key in data["asset_types"]]
            obj.allowed_asset_types.set(desired_assets)

            if created:
                self.stdout.write(f"  Created AccountType: {obj.name}")
            else:
                self.stdout.write(f"  Updated AccountType: {obj.name}")

        self.stdout.write("Seeding ClassificationDefinitions...")

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
                self.stdout.write(f"  Created Classification: {obj.name}")
            else:
                self.stdout.write(f"  Exists Classification: {obj.name}")

        self.stdout.write(
            self.style.SUCCESS(
                "System AccountTypes and Classifications seeded"
            )
        )
