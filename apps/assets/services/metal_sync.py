import logging
from decimal import Decimal

from assets.models.asset import Asset
from assets.models.metal_detail import MetalDetail
from external_data.fmp.metals import fetch_precious_metal_quote, fetch_metal_profile
from core.types import DomainType

logger = logging.getLogger(__name__)


class MetalSyncService:
    @staticmethod
    def sync(asset: Asset) -> bool:
        """
        Fetch data for a precious metal asset and update its MetalDetail.
        Returns True if sync succeeded, False otherwise.
        """
        if asset.asset_type != DomainType.METAL:
            logger.warning(
                f"Asset {asset.symbol} is not a metal, skipping sync")
            return False

        # 🛡️ Step 1: Validate it is truly a metal
        profile = fetch_metal_profile(asset.symbol)
        if not profile:
            logger.warning(f"No profile found for metal symbol {asset.symbol}")
            return False

        exchange = profile.get("exchangeShortName", "").lower()
        if exchange not in {"commodities", "metals", "precious metals"}:
            logger.warning(
                f"Symbol {asset.symbol} (exchange: {exchange}) is not recognized as a metal. "
                "Suggest adding it as a custom asset."
            )
            return False

        # ✅ Step 2: Fetch external quote
        data = fetch_precious_metal_quote(asset.symbol)
        if not data:
            logger.warning(f"Missing metal data for {asset.symbol}")
            return False

        # ✅ Step 3: Ensure detail exists
        detail, _ = MetalDetail.objects.get_or_create(asset=asset)

        try:
            detail.unit = data.get("unit", "oz")
            detail.currency = data.get("currency", "USD")

            price = data.get("price")
            detail.last_price = Decimal(
                str(price)) if price is not None else None

            detail.is_custom = False
            detail.save()
            logger.info(f"Synced metal {asset.symbol}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to sync metal {asset.symbol}: {e}", exc_info=True)
            return False
