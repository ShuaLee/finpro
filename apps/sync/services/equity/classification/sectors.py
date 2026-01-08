import logging

from django.db import transaction

from assets.models.classifications.sector import Sector
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.syncs.base import BaseSyncService

logger = logging.getLogger(__name__)


class SectorReferenceSyncService(BaseSyncService):
    """
    Sync equity sectors from the provider.

    Behavior:
    - Create missing sectors
    - NEVER delete sectors
    """

    name = "equity.reference.sectors"

    @transaction.atomic
    def _sync(self) -> dict:
        sectors = FMP_PROVIDER.get_available_sectors()

        created = 0
        unchanged = 0

        for name in sectors:
            name = (name or "").strip()
            if not name:
                continue

            _, was_created = Sector.objects.update_or_create(
                name=name,
            )

            if was_created:
                created += 1
            else:
                unchanged += 1

        logger.info(
            "[SECTOR_SYNC] created=%s unchanged=%s",
            created,
            unchanged,
        )

        return {
            "success": True,
            "created": created,
            "unchanged": unchanged,
        }
