from django.core.management.base import BaseCommand

from apps.assets.services import PublicAssetSyncService


class Command(BaseCommand):
    help = "Sync public assets from FMP for a supplied list of symbols."

    def add_arguments(self, parser):
        parser.add_argument("symbols", nargs="+", help="Ticker/pair symbols to sync into the local asset table.")
        parser.add_argument(
            "--asset-type",
            default="equity",
            help="System asset type slug to use for the synced assets (default: equity).",
        )

    def handle(self, *args, **options):
        result = PublicAssetSyncService.sync_symbols(
            symbols=options["symbols"],
            asset_type_slug=options["asset_type"],
        )
        self.stdout.write(self.style.SUCCESS(str(result)))
