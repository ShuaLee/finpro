import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.pricing import AssetPrice
from assets.models.pricing.extensions import EquityPriceExtension
from assets.services.utils import get_primary_ticker
from external_data.fmp.equities.fetchers import fetch_equity_quote

logger = logging.getLogger(__name__)


class EquityPriceSyncService:
    """
    Responsible ONLY for:
      - Price
      - Change
      - Volume
      - (other fast-moving fields if added later)

    This service does NOT:
      - Update profile metadata
      - Update identifiers
      - Perform universe reconciliation
      - Sync dividends
    """

    # =============================
    # PUBLIC ENTRYPOINT
    # =============================
    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> bool:
        if asset.asset_type.slug != "equity":
            return False

        ticker = get_primary_ticker(asset)
        if not ticker:
            logger.warning(f"[PRICE] No primary ticker for asset {asset.id}")
            return False

        data = fetch_equity_quote(ticker)
        if not data:
            logger.warning(f"[PRICE] No quote returned for {ticker}")
            EquityPriceSyncService._mark_asset_inactive(asset)
            return False

        EquityPriceSyncService._apply_quote(asset, data)
        return True

    # ---------------------------------------------------------
    # Write quote → AssetPrice + EquityPriceExtension
    # ---------------------------------------------------------
    @staticmethod
    def _apply_price_fields(asset: Asset, quote: dict):
        """
        Writes:
         - AssetPrice.price
         - EquityPriceExtension.change, change_percent, volume, avg_volume
        """

        # 1. Base price record
        asset_price, _ = AssetPrice.objects.get_or_create(
            asset=asset,
            defaults={"price": quote.get("price") or 0, "source": "FMP"}
        )

        if quote.get("price") is not None:
            asset_price.price = quote["price"]

        asset_price.source = "FMP"
        asset_price.save()

        # 2. Equity-specific extension
        ext, _ = EquityPriceExtension.objects.get_or_create(
            asset_price=asset_price
        )

        if "change" in quote:
            ext.change = quote["change"]

        if "changePercent" in quote:
            ext.change_percent = quote["changePercent"]

        if "volume" in quote:
            ext.volume = quote["volume"]

        if "avgVolume" in quote:
            ext.avg_volume = quote["avgVolume"]

        ext.save()

    # ---------------------------------------------------------
    # Mark delisted if price endpoint stops returning data
    # ---------------------------------------------------------
    @staticmethod
    def _mark_asset_inactive(asset: Asset):
        profile = getattr(asset, "equity_profile", None)
        if not profile:
            return

        if profile.is_actively_trading:
            profile.is_actively_trading = False
            profile.save()
