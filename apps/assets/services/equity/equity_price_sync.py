import logging
from django.db import transaction

from assets.models.equity import EquityAsset
from assets.models.core import AssetPrice
from external_data.providers.fmp.client import FMP_PROVIDER

logger = logging.getLogger(__name__)


class EquityPriceSyncService:
    """
    Updates prices for all equities.

    - No identity logic
    - No retries per asset
    - Stateless
    """

    @classmethod
    @transaction.atomic
    def sync_all(cls) -> int:
        updated = 0

        for equity in EquityAsset.objects.select_related("asset"):
            try:
                quote = FMP_PROVIDER.get_equity_quote(equity.ticker)
            except Exception:
                continue

            if quote.price is None:
                continue

            AssetPrice.objects.update_or_create(
                asset=equity.asset,
                defaults={
                    "price": quote.price,
                    "source": "FMP",
                },
            )
            updated += 1

        logger.info("[EQUITY_PRICE] Updated %s prices", updated)
        return updated
