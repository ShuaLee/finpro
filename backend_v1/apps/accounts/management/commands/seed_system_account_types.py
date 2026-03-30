from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models.account_type import AccountType
from assets.models.core import AssetType


class Command(BaseCommand):
    help = "Seed system AccountTypes"

    @staticmethod
    def _get_asset_type(slug):
        found = AssetType.objects.filter(slug=slug).first()
        if not found:
            raise AssetType.DoesNotExist(f"AssetType not found for slug: {slug}")
        return found

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding system AccountTypes...")

        asset_types = {
            "equity": self._get_asset_type("equity"),
            "crypto": self._get_asset_type("crypto"),
            "real_estate": self._get_asset_type("real_estate"),
            "precious_metal": self._get_asset_type("precious_metal"),
        }

        account_types = [
            {"name": "Brokerage", "slug": "brokerage", "asset_types": ["equity"]},
            {"name": "Cryptocurrency Wallet", "slug": "crypto-wallet", "asset_types": ["crypto"]},
            {"name": "Real Estate", "slug": "real-estate", "asset_types": ["real_estate"]},
            {"name": "Precious Metal", "slug": "precious-metal", "asset_types": ["precious_metal"]},
        ]

        for data in account_types:
            obj, created = AccountType.objects.get_or_create(
                slug=data["slug"],
                defaults={"name": data["name"], "is_system": True},
            )

            obj.name = data["name"]
            obj.is_system = True
            obj.owner = None
            obj.save()

            desired_assets = [asset_types[key] for key in data["asset_types"]]
            obj.allowed_asset_types.set(desired_assets)

            prefix = "Created" if created else "Updated"
            self.stdout.write(f"  {prefix} AccountType: {obj.name}")

        self.stdout.write(
            self.style.SUCCESS("System AccountTypes seeded")
        )
