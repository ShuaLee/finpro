import logging

from django.db import transaction

from assets.models.classifications.industry import Industry
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.syncs.base import BaseSyncService


logger = logging.getLogger(__name__)


class IndustryReferenceSyncService(BaseSyncService):
    """
    Sync equity industries from the provider.

    Behavior:
    - Create missing industries
    - NEVER delete industries
    """

    name = "equity.reference.industries"

    @transaction.atomic
    def _sync(self) -> dict:
        industries = FMP_PROVIDER.get_available_industries()

        created = 0
        unchanged = 0

        for name in industries:
            name = (name or "").strip()
            if not name:
                continue

            _, was_created = Industry.objects.update_or_create(
                name=name,
            )

            if was_created:
                created += 1
            else:
                unchanged += 1

        logger.info(
            "[INDUSTRY_SYNC] created=%s unchanged=%s",
            created,
            unchanged,
        )

        return {
            "success": True,
            "created": created,
            "unchanged": unchanged,
        }
