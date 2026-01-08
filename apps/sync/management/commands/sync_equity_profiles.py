import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from assets.models.asset_core import Asset
from sync.services.syncs.equity.profile import EquityProfileSyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync equity profiles for all equity assets"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of equities to sync (dev only)",
        )
        parser.add_argument(
            "--only-active",
            action="store_true",
            help="Only sync equities currently marked as active",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force profile sync even if unchanged",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        only_active = options["only_active"]
        force = options["force"]

        self.stdout.write(
            self.style.WARNING(
                "[SYNC_EQUITY_PROFILES] Starting equity profile sync"
            )
        )

        qs = Asset.objects.filter(
            asset_type__slug="equity"
        )

        if only_active:
            qs = qs.filter(
                profiles__is_actively_trading=True
            )

        qs = qs.distinct().order_by("created_at")

        if limit:
            qs = qs[:limit]

        service = EquityProfileSyncService(force=force)

        total = 0
        success = 0
        failed = 0

        for asset in qs.iterator():
            total += 1
            try:
                result = service.sync(asset)
                if result.get("success"):
                    success += 1
                else:
                    failed += 1
            except Exception as exc:
                failed += 1
                logger.exception(
                    "[SYNC_EQUITY_PROFILES] Asset %s failed: %s",
                    asset.id,
                    exc,
                )

        self.stdout.write(self.style.SUCCESS(
            "[SYNC_EQUITY_PROFILES] Completed"
        ))
        self.stdout.write(
            f"  Total: {total}\n"
            f"  Success: {success}\n"
            f"  Failed: {failed}"
        )
