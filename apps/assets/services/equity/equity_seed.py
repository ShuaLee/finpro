import logging
from django.db import transaction

from assets.models.core import Asset
from assets.models.equity import EquityAsset
from assets.models.core import AssetType
from assets.services.equity.equity_factory import EquityAssetFactory
from external_data.providers.fmp.client import FMP_PROVIDER

logger = logging.getLogger(__name__)


class EquityUniverseSeeder:
    """
    Rebuilds the entire equity universe from the provider.

    - Truncates existing equities
    - Recreates only actively traded equities
    - Safe to run multiple times per day
    """

    @classmethod
    @transaction.atomic
    def rebuild(cls) -> int:
        logger.info("[EQUITY_SEED] Rebuilding equity universe")

        # Remove old universe
        EquityAsset.objects.all().delete()
        Asset.objects.filter(asset_type__slug="equity").delete()

        equity_type = AssetType.objects.get(slug="equity")
        rows = FMP_PROVIDER.get_actively_traded_equities()

        created = 0

        for row in rows:
            ticker = (row.get("symbol") or "").strip().upper()
            if not ticker:
                continue

            EquityAssetFactory.create(
                ticker=ticker,
                name=row.get("name") or ticker,
            )
            created += 1

        logger.info("[EQUITY_SEED] Created %s equities", created)
        return created
