import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
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
            self.style.NOTICE("[SEED_EQUITIES] Starting equity seed")
        )

        try:
            rows = FMP_PROVIDER.get_actively_traded_equities()
        except ExternalDataError as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"[SEED_EQUITIES] Failed to fetch active equities: {exc}"
                )
            )
            return

        if limit:
            rows = rows[:limit]

        try:
            equity_type = AssetType.objects.get(slug="equity")
        except AssetType.DoesNotExist:
            self.stderr.write(
                self.style.ERROR("AssetType 'equity' does not exist.")
            )
            return

        created_assets = 0
        existing_assets = 0
        created_identifiers = 0

        for item in rows:
            ticker = (item.get("symbol") or "").strip().upper()
            if not ticker:
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would seed equity {ticker}"
                )
                continue

            with transaction.atomic():
                # -----------------------------------------
                # Resolve or create Asset via identifier
                # -----------------------------------------
                ident = AssetIdentifier.objects.filter(
                    id_type=AssetIdentifier.IdentifierType.TICKER,
                    value=ticker,
                ).select_related("asset").first()

                if ident:
                    asset = ident.asset
                    existing_assets += 1
                else:
                    asset = Asset.objects.create(
                        asset_type=equity_type,
                    )
                    AssetIdentifier.objects.create(
                        asset=asset,
                        id_type=AssetIdentifier.IdentifierType.TICKER,
                        value=ticker,
                    )
                    created_assets += 1
                    created_identifiers += 1

        self.stdout.write(self.style.SUCCESS("[SEED_EQUITIES] Completed"))
        self.stdout.write(
            f"  Assets created: {created_assets}\n"
            f"  Assets existing: {existing_assets}\n"
            f"  Identifiers created: {created_identifiers}"
        )
