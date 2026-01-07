import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from assets.models.asset_core import AssetType
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.exceptions import ExternalDataError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed actively traded equity assets from FMP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of equities to seed (for development)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not write to database",
        )

    # --------------------------------------------------
    # Entry point
    # --------------------------------------------------
    def handle(self, *args, **options):
        limit = options["limit"]
        dry_run = options["dry_run"]

        self.stdout.write(
            self.style.NOTICE(
                "[SEED_EQUITIES] Starting equity seed"
            )
        )

        try:
            symbols = FMP_PROVIDER.get_actively_traded_list()
        except ExternalDataError as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"[SEED_EQUITIES] Failed to fetch active equities: {exc}"
                )
            )
            return

        if limit:
            symbols = symbols[:limit]

        equity_type = AssetType.objects.get(slug="equity")

        created_assets = 0
        existing_assets = 0
        created_identifiers = 0

        for item in symbols:
            ticker = item.get("symbol")
            name = item.get("name")

            if not ticker:
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would seed equity {ticker}"
                )
                continue

            with transaction.atomic():
                asset, created = Asset.objects.get_or_create(
                    asset_type=equity_type,
                    defaults={
                        "name": name or ticker,
                        "is_actively_trading": True,
                    },
                )

                if created:
                    created_assets += 1
                else:
                    existing_assets += 1

                # Ensure actively trading flag is correct
                if not asset.is_actively_trading:
                    asset.is_actively_trading = True
                    asset.save(update_fields=["is_actively_trading"])

                # Ensure ticker identifier exists
                ident, ident_created = AssetIdentifier.objects.get_or_create(
                    asset=asset,
                    id_type=AssetIdentifier.IdentifierType.TICKER,
                    defaults={"value": ticker.upper()},
                )

                if ident_created:
                    created_identifiers += 1

        self.stdout.write(
            self.style.SUCCESS(
                "[SEED_EQUITIES] Completed"
            )
        )
        self.stdout.write(
            f"  Assets created: {created_assets}\n"
            f"  Assets existing: {existing_assets}\n"
            f"  Identifiers created: {created_identifiers}"
        )
