# sync/management/commands/sync_equity_profiles.py
from django.core.management.base import BaseCommand

from assets.models.asset_core import Asset
from sync.services.equity.profile import EquityProfileSyncService


class Command(BaseCommand):
    help = "Sync equity profiles (single-ticker calls)"

    def add_arguments(self, parser):
        parser.add_argument("--only-active", action="store_true")
        parser.add_argument("--limit", type=int)

    def handle(self, *args, **opts):
        qs = Asset.objects.filter(asset_type__slug="equity")

        if opts["only_active"]:
            qs = qs.filter(profiles__is_actively_trading=True)

        if opts["limit"]:
            qs = qs[:opts["limit"]]

        service = EquityProfileSyncService()

        for asset in qs.iterator():
            service.sync(asset)

        self.stdout.write(self.style.SUCCESS("Profile sync complete"))
