# sync/management/commands/seed_equities.py
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier, AssetType
from external_data.providers.fmp.client import FMP_PROVIDER

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed actively traded equity tickers (create missing only)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        limit = opts.get("limit")
        dry_run = opts.get("dry_run")

        rows = FMP_PROVIDER.get_actively_traded_equities()
        if limit:
            rows = rows[:limit]

        equity_type = AssetType.objects.get(slug="equity")

        created = existing = 0

        for row in rows:
            ticker = (row.get("symbol") or "").upper().strip()
            if not ticker:
                continue

            ident = AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=ticker,
            ).select_related("asset").first()

            if ident:
                existing += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would create {ticker}")
                continue

            with transaction.atomic():
                asset = Asset.objects.create(asset_type=equity_type)
                AssetIdentifier.objects.create(
                    asset=asset,
                    id_type=AssetIdentifier.IdentifierType.TICKER,
                    value=ticker,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete — created={created}, existing={existing}"
        ))
