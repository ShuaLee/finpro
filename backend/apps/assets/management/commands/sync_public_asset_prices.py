from django.core.management.base import BaseCommand

from apps.assets.models import Asset
from apps.assets.services import PublicAssetSyncService


class Command(BaseCommand):
    help = "Refresh latest prices for tracked public assets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--asset-type",
            default=None,
            help="Optional asset type slug to limit the refresh scope.",
        )
        parser.add_argument(
            "--symbols",
            nargs="*",
            default=None,
            help="Optional explicit symbol list to refresh.",
        )

    def handle(self, *args, **options):
        queryset = Asset.objects.filter(owner__isnull=True).select_related("market_data")
        default_price_types = ["equity", "crypto", "cryptocurrency", "commodity", "precious_metal"]

        if options["asset_type"]:
            queryset = queryset.filter(asset_type__slug=options["asset_type"])
        else:
            queryset = queryset.filter(asset_type__slug__in=default_price_types)

        symbols = options.get("symbols") or []
        if symbols:
            normalized = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
            queryset = queryset.filter(symbol__in=normalized)
        else:
            queryset = queryset.filter(market_data__status__in=["tracked", "stale"])

        result = PublicAssetSyncService.refresh_quotes_for_assets(assets=list(queryset))
        self.stdout.write(self.style.SUCCESS(str(result)))
