import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetIdentifier
from assets.models.pricing import AssetPrice
from external_data.exceptions import ExternalDataEmptyResult, ExternalDataError
from external_data.providers.fmp.client import FMP_PROVIDER
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class EquityPriceSyncService(BaseSyncService):
    """
    Syncs the latest equity price.

    Responsibilities:
    - Fetch quote for ticker
    - Update AssetPrice
    - Soft-signal inactive assets

    Does NOT:
    - Change identifiers
    - Handle renames
    - Guess replacements
    """

    name = "equity.price"

    @transaction.atomic
    def _sync(self, asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity_asset"}

        ticker = self._get_ticker(asset)
        if not ticker:
            return {
                "success": False,
                "error": "missing_ticker"
            }
        
        provider = FMP_PROVIDER

        try:
            quote = provider.get_equity_quote(ticker)
        except ExternalDataEmptyResult:
            logger.warning(
                "[PRICE_SYNC] No quote returned for %s (asset=%s)",
                ticker,
                asset.id,
            )
            return {
                "success": False,
                "error": "quote_not_found",
            }
        except ExternalDataError:
            # Provider error should bubble up (circuit breaker, retries, etc.)
            raise

        if quote.price is None:
            return {
                "success": False,
                "error": "empty_price",
            }
        
        AssetPrice.objects.update_or_create(
            asset=asset,
            defaults={
                "price": quote.price,
                "source": provider.name,
            },
        )

        return {
            "success": True,
            "price": str(quote.price),
        }


    # ==================================================
    # Helpers
    # ==================================================
    def _get_ticker(self, asset: Asset) -> str | None:
        """
        Return the equity ticker for the asset.
        """
        ident = asset.identifiers.filter(
            id_type=AssetIdentifier.IdentifierType.TICKER
        ).first()

        return ident.value.upper() if ident else None
