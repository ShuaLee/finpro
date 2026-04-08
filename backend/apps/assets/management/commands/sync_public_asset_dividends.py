from django.core.management.base import BaseCommand

from apps.assets.models import Asset
from apps.assets.services import AssetDividendService


class Command(BaseCommand):
    help = "Refresh dividend snapshots for tracked public equity assets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--symbols",
            nargs="*",
            default=None,
            help="Optional explicit symbol list to refresh.",
        )

    def handle(self, *args, **options):
        queryset = Asset.objects.filter(
            owner__isnull=True,
            asset_type__slug="equity",
            market_data__status__in=["tracked", "stale", "needs_review"],
        ).select_related("market_data", "price", "asset_type")

        symbols = options.get("symbols") or []
        if symbols:
            normalized = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
            queryset = queryset.filter(symbol__in=normalized)

        result = AssetDividendService.sync_assets(assets=list(queryset))
        self.stdout.write(self.style.SUCCESS(str(result)))
